/*
 * Qt WebChannel v5.15.2
 * License: LGPL-3.0 OR GPL-2.0 OR GPL-3.0
 */
"use strict";

var QWebChannel = function (transport, initCallback) {
    if (typeof transport !== "object" || typeof transport.send !== "function") {
        console.error("The QWebChannel expects a transport object with a send function and onmessage callback property.");
        return;
    }

    var channel = this;
    this.transport = transport;

    this.send = function (data) {
        if (typeof data !== "string") {
            data = JSON.stringify(data);
        }
        channel.transport.send(data);
    }

    this.transport.onmessage = function (message) {
        var data = message.data;
        if (typeof data === "string") {
            data = JSON.parse(data);
        }
        switch (data.type) {
            case QWebChannelMessageTypes.signal:
                channel.handleSignal(data);
                break;
            case QWebChannelMessageTypes.response:
                channel.handleResponse(data);
                break;
            case QWebChannelMessageTypes.propertyUpdate:
                channel.handlePropertyUpdate(data);
                break;
            default:
                console.error("invalid message received:", message.data);
                break;
        }
    }

    this.execCallbacks = {};
    this.execId = 0;
    this.exec = function (data, callback) {
        if (!callback) {
            // if no callback is given, send directly
            channel.send(data);
            return;
        }
        var execId = channel.execId++;
        data.id = execId;
        channel.execCallbacks[execId] = callback;
        channel.send(data);
    }

    this.objects = {};

    this.handleSignal = function (message) {
        var object = channel.objects[message.object];
        if (object) {
            object.signalEmitted(message.signal, message.args);
        } else {
            console.warn("Unhandled signal: " + message.object + "::" + message.signal);
        }
    }

    this.handleResponse = function (message) {
        if (!message.hasOwnProperty("id")) {
            console.error("Invalid response message received: ", message);
            return;
        }
        channel.execCallbacks[message.id](message.data);
        delete channel.execCallbacks[message.id];
    }

    this.handlePropertyUpdate = function (message) {
        for (var i in message.data) {
            var data = message.data[i];
            var object = channel.objects[data.object];
            if (object) {
                object.propertyUpdate(data.signals, data.properties);
            } else {
                console.warn("Unhandled property update: " + data.object + "::" + data.signal);
            }
        }
        channel.execCallbacks[message.id](message.data);
        delete channel.execCallbacks[message.id];
    }

    this.debug = function (message) {
        channel.send({ type: QWebChannelMessageTypes.debug, data: message });
    };

    channel.exec({ type: QWebChannelMessageTypes.init }, function (data) {
        for (var objectName in data) {
            var object = new QObject(objectName, data[objectName], channel);
        }
        // now unwrap properties, which might reference other registered objects
        for (var objectName in channel.objects) {
            channel.objects[objectName].unwrapProperties();
        }
        if (initCallback) {
            initCallback(channel);
        }
    });
};

var QWebChannelMessageTypes = {
    signal: 1,
    propertyUpdate: 2,
    init: 3,
    idle: 4,
    debug: 5,
    invokeMethod: 6,
    connectToSignal: 7,
    disconnectFromSignal: 8,
    setProperty: 9,
    response: 10,
};

var QObject = function (name, data, webChannel) {
    this.__id__ = name;
    webChannel.objects[name] = this;

    // List of callbacks that get invoked upon signal emission
    this.__objectSignals__ = {};

    // Cache of all properties, indexed by name
    this.__propertyCache__ = {};

    var object = this;

    // ----------------------------------------------------------------------
    // connection to the web channel
    this.unwrapQObject = function (response) {
        if (response instanceof Array) {
            // support list of objects
            var ret = new Array(response.length);
            for (var i = 0; i < response.length; i++) {
                ret[i] = object.unwrapQObject(response[i]);
            }
            return ret;
        }
        if (!response
            || !response["__QObject*__"]
            || response.id === undefined) {
            return response;
        }

        var objectId = response.id;
        if (webChannel.objects[objectId])
            return webChannel.objects[objectId];

        if (!response.data) {
            console.error("Cannot unwrap unknown QObject " + objectId + " without data.");
            return;
        }

        var qObject = new QObject(objectId, response.data, webChannel);
        qObject.destroyed.connect(function () {
            if (webChannel.objects[objectId] === qObject) {
                delete webChannel.objects[objectId];
                // reset the now deleted QObject to null
                var propertyValue = qObject.__propertyCache__[objectId];
                // TODO: what to do here?
            }
        });
        return qObject;
    }

    this.unwrapProperties = function () {
        for (var propertyIdx in data.properties) {
            object.__propertyCache__[propertyIdx] = object.unwrapQObject(data.properties[propertyIdx]);
        }
    }

    this.propertyUpdate = function (signals, map) {
        for (var propertyIdx in map) {
            var property = map[propertyIdx];
            object.__propertyCache__[propertyIdx] = object.unwrapQObject(property);
        }

        for (var signalName in signals) {
            var signal = object[signalName];
            if (signal) {
                signal(signals[signalName]);
            }
        }
    }

    this.signalEmitted = function (signalName, signalArgs) {
        var signal = object[signalName];

        if (!signal) {
            console.warn("signalEmitted event for unknown signal: " + signalName);
            return;
        }

        var unwrappedArgs = [];
        for (var i = 0; i < signalArgs.length; i++) {
            unwrappedArgs.push(object.unwrapQObject(signalArgs[i]));
        }

        signal.apply(object, unwrappedArgs);
    }

    this.addSignal = function (signalName, isPropertyNotifySignal) {
        var signal = function () {
            var signalArgs = [];
            for (var i = 0; i < arguments.length; i++) {
                signalArgs.push(arguments[i]);
            }
            // Check if anyone is connected to this signal
            var handlers = object.__objectSignals__[signalName];
            if (handlers) {
                handlers.forEach(function (handler) {
                    handler.apply(object, signalArgs);
                });
            }
        };

        signal.connect = function (callback) {
            if (typeof callback !== "function") {
                console.error("Bad callback given to connect to signal " + signalName);
                return;
            }

            if (!object.__objectSignals__[signalName]) {
                object.__objectSignals__[signalName] = [];
                if (!isPropertyNotifySignal) {
                    webChannel.send({
                        type: QWebChannelMessageTypes.connectToSignal,
                        object: object.__id__,
                        signal: signalName
                    });
                }
            }
            object.__objectSignals__[signalName].push(callback);
        };

        signal.disconnect = function (callback) {
            if (typeof callback !== "function") {
                console.error("Bad callback given to disconnect from signal " + signalName);
                return;
            }
            var handlers = object.__objectSignals__[signalName];
            var index = handlers.indexOf(callback);
            if (index > -1) {
                handlers.splice(index, 1);
                if (handlers.length === 0 && !isPropertyNotifySignal) {
                    webChannel.send({
                        type: QWebChannelMessageTypes.disconnectFromSignal,
                        object: object.__id__,
                        signal: signalName
                    });
                    delete object.__objectSignals__[signalName];
                }
            }
        };

        object[signalName] = signal;
    }

    this.addProperty = function (propertyName) {
        var propertyNotifySignalName = propertyName + "Changed";
        if (!data.signals[propertyNotifySignalName]) {
            // only add notify signal if it isn't part of the signal definitions
            object.addSignal(propertyNotifySignalName, true);
        }

        // Define getter/setter
        Object.defineProperty(object, propertyName, {
            configurable: true,
            get: function () {
                return object.__propertyCache__[propertyName];
            },
            set: function (value) {
                if (value === undefined) value = null;
                // Update local cache
                object.__propertyCache__[propertyName] = value;
                // Send update to server
                webChannel.send({
                    type: QWebChannelMessageTypes.setProperty,
                    object: object.__id__,
                    property: propertyName,
                    value: value
                });
            }
        });
    }

    this.addMethod = function (methodName) {
        object[methodName] = function () {
            var args = [];
            for (var i = 0; i < arguments.length; i++) {
                args.push(arguments[i]);
            }

            var callback = null;
            if (typeof args[args.length - 1] === "function") {
                callback = args.pop();
            }

            webChannel.exec({
                "type": QWebChannelMessageTypes.invokeMethod,
                "object": object.__id__,
                "method": methodName,
                "args": args
            }, function (response) {
                if (response !== undefined) {
                    var result = object.unwrapQObject(response);
                    if (callback) {
                        (callback)(result);
                    }
                }
            });
        };
    }

    // Process metadata
    for (var signalName in data.signals) {
        object.addSignal(signalName);
    }
    for (var propertyName in data.properties) {
        object.addProperty(propertyName);
    }
    for (var methodName in data.methods) {
        object.addMethod(methodName);
    }
};

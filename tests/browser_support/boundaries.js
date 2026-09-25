// Installed before navigation/imports. Finite draws fail loudly on exhaustion.
(() => {
    const draws = [0.25, 0.75, 0.5, 0.125, 0.875, 0.375];
    Math.random = () => {
        if (!draws.length) throw new Error('Deterministic random sequence exhausted');
        return draws.shift();
    };
    class RecordingWebSocket extends EventTarget {
        static CONNECTING = 0;
        static OPEN = 1;
        static CLOSING = 2;
        static CLOSED = 3;
        constructor(url) {
            super();
            this.url = url;
            this.readyState = 0;
            this.sent = [];
            window.testSockets.push(this);
        }
        emit(type, event) {
            this.dispatchEvent(event);
            this['on' + type]?.(event);
        }
        open() {
            this.readyState = 1;
            this.emit('open', new Event('open'));
        }
        send(value) {
            if (this.readyState !== 1) throw new Error('Socket is not open');
            this.sent.push(value);
        }
        receive(value) {
            this.emit('message', new MessageEvent('message', {data: value}));
        }
        close() {
            this.readyState = 3;
            this.emit('close', new CloseEvent('close'));
        }
    }
    window.testSockets = [];
    window.WebSocket = RecordingWebSocket;
})();

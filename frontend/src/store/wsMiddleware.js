import { ratesUpdated } from "./liveRatesSlice";

export const wsConnect = (url) => ({ type: "ws/connect", payload: url });

export function createWsMiddleware() {
  return (storeApi) => {
    let socket = null;
    let retry = 1000;

    const connect = (url) => {
      socket = new WebSocket(url);
      socket.onmessage = (event) => {
        storeApi.dispatch(ratesUpdated(JSON.parse(event.data)));
      };
      socket.onopen = () => { retry = 1000; };
      socket.onclose = () => {
        setTimeout(() => connect(url), retry);
        retry = Math.min(retry * 2, 30000);
      };
    };

    return (next) => (action) => {
      if (action.type === "ws/connect") {
        if (socket) socket.close();
        connect(action.payload);
        return;
      }
      return next(action);
    };
  };
}

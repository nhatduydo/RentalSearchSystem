import { useEffect, useRef, useState } from 'react';

const useWebSocket = (roomId, userId) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(`wss://system-accommodation.ap.ngrok.io/ws/chat/${roomId}/`);

    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [data, ...prev]);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.current?.close();
    };
  }, [roomId]);

  const sendMessage = (text) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({
        message: text,
        sender_id: userId,
      }));

      setMessages(prev => [
        { message: text, sender_id: userId },
        ...prev,
      ]);
    }
  };

  return { messages, sendMessage, isConnected };
};

export default useWebSocket;

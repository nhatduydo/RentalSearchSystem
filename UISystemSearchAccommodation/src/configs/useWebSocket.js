import { useEffect, useRef, useState } from 'react';

const WS_URL = 'wss://systemaccommodation.online';

const useWebSocket = ({ roomId, token }) => {
  const socketRef = useRef(null);
  const [status, setStatus] = useState('Disconnected');
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    if (!roomId || !token) return;

    const wsUrl = `${WS_URL}/ws/chat/${roomId}/?token=${token}`;
    socketRef.current = new WebSocket(wsUrl);

    setStatus('Connecting...');

    socketRef.current.onopen = () => {
      setStatus('Connected');
    };

    socketRef.current.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        console.log('Message received:', data);
        setLastMessage(data); // chỉ lưu message cuối cùng
      } catch (err) {
        console.error('Message parse error:', err);
      }
    };

    socketRef.current.onclose = (e) => {
      setStatus(`Disconnected (code: ${e.code})`);
    };

    socketRef.current.onerror = (e) => {
      console.error('WebSocket error:', e.message || e);
      setStatus('Error');
    };

    return () => {
      socketRef.current?.close();
    };
  }, [roomId, token]);

  const sendMessage = (message) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ message }));
    } else {
      console.warn('WebSocket is not open');
    }
  };

  return { sendMessage, status, lastMessage };
};

export default useWebSocket;

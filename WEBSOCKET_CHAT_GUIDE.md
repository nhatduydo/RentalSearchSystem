# Hướng dẫn tích hợp WebSocket Chat vào React Native

## 1. Cài đặt thư viện
```bash
npm install react-native-websocket
```

## 2. Tạo Custom Hook (useWebSocket.js)
```javascript
import { useEffect, useRef, useState } from 'react';

const useWebSocket = (roomId) => {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Kết nối WebSocket
    ws.current = new WebSocket(`wss://8183-103-199-70-79.ngrok-free.app/ws/chat/${roomId}/`);

    // Xử lý sự kiện kết nối
    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket Connected');
    };

    // Xử lý tin nhắn nhận được
    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    // Xử lý lỗi
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Xử lý đóng kết nối
    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket Disconnected');
    };

    // Cleanup khi component unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [roomId]);

  // Hàm gửi tin nhắn
  const sendMessage = (message, senderId) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({
        message,
        sender_id: senderId
      }));
    }
  };

  return {
    messages,
    isConnected,
    sendMessage
  };
};

export default useWebSocket;
```

## 3. Tạo Component Chat (ChatScreen.js)
```javascript
import React, { useState } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import useWebSocket from './useWebSocket';

const ChatScreen = ({ route }) => {
  const { roomId, userId } = route.params;
  const [message, setMessage] = useState('');
  const { messages, isConnected, sendMessage } = useWebSocket(roomId);

  const handleSend = () => {
    if (message.trim()) {
      sendMessage(message, userId);
      setMessage('');
    }
  };

  const renderMessage = ({ item }) => (
    <View style={[
      styles.messageContainer,
      item.sender_id === userId ? styles.sentMessage : styles.receivedMessage
    ]}>
      <Text style={styles.messageText}>{item.message}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.status}>
        {isConnected ? 'Connected' : 'Disconnected'}
      </Text>
      
      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(_, index) => index.toString()}
        style={styles.messageList}
      />

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={message}
          onChangeText={setMessage}
          placeholder="Type a message..."
        />
        <TouchableOpacity 
          style={styles.sendButton}
          onPress={handleSend}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  status: {
    padding: 10,
    textAlign: 'center',
    backgroundColor: '#e0e0e0',
  },
  messageList: {
    flex: 1,
    padding: 10,
  },
  messageContainer: {
    maxWidth: '80%',
    padding: 10,
    marginVertical: 5,
    borderRadius: 10,
  },
  sentMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  receivedMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#E5E5EA',
  },
  messageText: {
    color: '#000',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 8,
    marginRight: 10,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    borderRadius: 20,
    paddingHorizontal: 20,
    justifyContent: 'center',
  },
  sendButtonText: {
    color: '#fff',
  },
});

export default ChatScreen;
```

## 4. Thêm vào Navigation
```javascript
<Stack.Screen 
  name="Chat" 
  component={ChatScreen}
  initialParams={{ roomId: 'room1', userId: 'user1' }}
/>
```

## Cách sử dụng:
1. Copy các file trên vào project React Native
2. Thêm màn hình Chat vào navigation
3. Truyền `roomId` và `userId` khi navigate đến màn hình Chat:
```javascript
navigation.navigate('Chat', {
  roomId: 'room1',  // ID phòng chat
  userId: 'user1'   // ID người dùng
});
```

## Lưu ý:
- URL WebSocket (`wss://8183-103-199-70-79.ngrok-free.app/ws/chat/`) cần được cập nhật khi ngrok thay đổi
- Đảm bảo backend Django đang chạy và WebSocket đã được cấu hình đúng
- Test kết nối trước khi triển khai

## Test WebSocket:
1. Chạy backend Django:
```bash
uvicorn accommodationSearchApp.asgi:application --reload
```

2. Test WebSocket với wscat:
```bash
npx wscat -c wss://8183-103-199-70-79.ngrok-free.app/ws/chat/room1/
```

3. Gửi tin nhắn test:
```json
{"message": "Test message", "sender_id": "user1"}
``` 
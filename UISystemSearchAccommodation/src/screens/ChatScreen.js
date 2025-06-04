import React, { useState, useEffect } from 'react';
import {
  FlatList,
  Image,
  SafeAreaView,
  StatusBar,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  KeyboardAvoidingView,
  TouchableWithoutFeedback,
  Keyboard,
  Platform,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { chatStyles } from '../styles/chatStyles';
import useWebSocket from '../configs/useWebSocket';
import axios, { endpoints } from '../configs/Apis';


const ChatScreen = ({ navigation, route }) => {
  const { roomId, userId, token, partner } = route.params;
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');

  //console.log("partner-->", partner);

  const { sendMessage, status, lastMessage } = useWebSocket({ roomId, token });

  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${endpoints['chat-rooms']}${roomId}/messages/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      //console.log(res.data.results + roomId);
      setMessages(res.data.results.reverse());
    } catch (err) {
      console.error('Lỗi khi lấy tin nhắn:', err.message);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, [roomId]);

  useEffect(() => {
    if (lastMessage) {
      setMessages((prev) => {
        const exists = prev.some((msg) => msg.id === lastMessage.id);
        return exists ? prev : [lastMessage, ...prev];
      });
    }
  }, [lastMessage]);


  const handleSend = async () => {
    if (!message.trim()) return;
    try {
      await axios.post(
        `${endpoints['chat-rooms']}${roomId}/messages/`,
        { content: message.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage('');

      fetchMessages();
    } catch (err) {
      console.error('Lỗi khi gửi tin nhắn:', err.message);
    }
  };


  const renderItem = ({ item }) => {
    //console.log('sender.id:', item.sender?.id, '| userId:', userId);
    return (<View
      style={[
        chatStyles.messageContainer,
        parseInt(item.sender?.id) === parseInt(userId)
          ? chatStyles.myMessage : chatStyles.otherMessage,
      ]}>
      <Text style={chatStyles.messageText}>{item.content}</Text>
      <Text style={chatStyles.timestamp}>
        {new Date(item.created_date).toLocaleTimeString()}
      </Text>
    </View>);
  };

  return (
    <SafeAreaView style={{ flex: 1 }}>
      <StatusBar backgroundColor="#2196F3" barStyle="light-content" />

      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <View style={{ flex: 1 }}>
          <View style={chatStyles.header}>
            <Image source={{ uri: partner.avatar }} style={chatStyles.avatar} />
            <Text style={chatStyles.name}>
              Đang chat với {partner.firstName} {partner.lastName}
            </Text>
          </View>

          <FlatList
            style={{ flex: 1 }}
            data={messages}
            renderItem={renderItem}
            keyExtractor={(item) => item.id?.toString()}
            contentContainerStyle={{ padding: 10 }}
            inverted
            keyboardShouldPersistTaps="handled"
          />

          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
          >
            <View style={chatStyles.inputContainer}>
              <TextInput
                style={chatStyles.input}
                placeholder="Nhập tin nhắn..."
                value={message}
                onChangeText={setMessage}
              />
              <TouchableOpacity onPress={handleSend}>
                <Icon name="send" size={24} color="#2196F3" />
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </View>
      </TouchableWithoutFeedback>
    </SafeAreaView>
  );
};

export default ChatScreen;

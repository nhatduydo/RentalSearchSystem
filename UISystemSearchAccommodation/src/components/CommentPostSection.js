import React, { useEffect, useState } from 'react';
import { Modal, View, Text, FlatList, ActivityIndicator, StyleSheet, TouchableOpacity, Image, TextInput } from 'react-native';
import axios from '../configs/Apis';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { FontAwesome, Ionicons } from '@expo/vector-icons';

const CommentPostSection = ({ visible, onClose, postId }) => {
    const [comments, setComments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [inputValue, setInputValue] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [replyTo, setReplyTo] = useState(null);

    useEffect(() => {
        if (visible) {
            fetchComments();
        }
    }, [visible]);

    const fetchComments = async () => {
        try {
            setLoading(true);
            const token = await AsyncStorage.getItem('access_token');
            const res = await axios.get(`/posts/${postId}/comments/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setComments(res.data);
        } catch (err) {
            console.error("Lỗi khi lấy bình luận:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleSendComment = async () => {
        if (!inputValue.trim()) return;
        setSubmitting(true);

        try {
            const token = await AsyncStorage.getItem('access_token');
            const res = await axios.post('/comments/', {
                post: postId,
                content: inputValue,
                parent: replyTo,
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (replyTo) {
                setComments(prev =>
                    prev.map(comment =>
                        comment.id === replyTo
                            ? { ...comment, replies: [res.data, ...comment.replies] }
                            : comment
                    )
                );
            } else {
                setComments(prev => [res.data, ...prev]);
            }

            setInputValue('');
            setReplyTo(null);
        } catch (err) {
            console.error("Lỗi khi gửi bình luận:", err);
        } finally {
            setSubmitting(false);
        }
    };

    const handleLike = async (commentId) => {
        // Cập nhật UI ngay lập tức, toggle like
        setComments(prevComments =>
            prevComments.map(comment => {
                if (comment.id === commentId) {
                    return { ...comment, like: !comment.like };
                } else if (comment.replies?.length) {
                    return {
                        ...comment,
                        replies: comment.replies.map(reply =>
                            reply.id === commentId ? { ...reply, like: !reply.like } : reply
                        ),
                    };
                }
                return comment;
            })
        );

        try {
            const token = await AsyncStorage.getItem('access_token');
            await axios.post(`/comments/${commentId}/like/`, {}, {
                headers: { Authorization: `Bearer ${token}` },
            });
        } catch (err) {
            console.error("Lỗi khi like comment:", err);
            setComments(prevComments =>
                prevComments.map(comment => {
                    if (comment.id === commentId) {
                        return { ...comment, like: !comment.like };
                    } else if (comment.replies?.length) {
                        return {
                            ...comment,
                            replies: comment.replies.map(reply =>
                                reply.id === commentId ? { ...reply, like: !reply.like } : reply
                            ),
                        };
                    }
                    return comment;
                })
            );
        }
    };

    const CommentItem = ({ comment }) => (
        <View style={{ marginBottom: 12 }}>
            <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
                <Image source={{ uri: comment.user.avatar }} style={styles.avatar} />
                <View style={styles.commentBox}>
                    <Text style={styles.username}>{comment.user.first_name} {comment.user.last_name}</Text>
                    <Text>{comment.content}</Text>
                    <View style={styles.actions}>
                        <TouchableOpacity onPress={() => handleLike(comment.id)}>
                            <Ionicons
                                name={comment.like ? 'heart' : 'heart-outline'}
                                size={18}
                                color={comment.like ? 'red' : 'gray'}
                            />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => setReplyTo(comment.id)}>
                            <Text style={styles.replyText}>Trả lời</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </View>
            {comment.replies?.length > 0 && renderReplies(comment.replies)}
        </View>
    );

    const renderReplies = (replies) => {
        return replies.map(reply => (
            <View key={reply.id} style={{ marginLeft: 40, marginTop: 8 }}>
                <CommentItem comment={reply} />
            </View>
        ));
    };


    return (
        <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
            <View style={styles.modalBackground}>
                <View style={styles.modalContainer}>
                    <View style={styles.header}>
                        <Text style={styles.title}>Bình luận</Text>
                        <TouchableOpacity onPress={onClose}>
                            <Ionicons name="close" size={24} color="#000" />
                        </TouchableOpacity>
                    </View>

                    {loading ? (
                        <ActivityIndicator size="large" color="#000" />
                    ) : (
                        <FlatList
                            data={comments}
                            keyExtractor={(item) => item.id.toString()}
                            renderItem={({ item }) => <CommentItem comment={item} />}
                            contentContainerStyle={{ paddingBottom: 70 }}
                        />
                    )}

                    <View style={styles.inputContainer}>
                        <TextInput
                            style={styles.input}
                            placeholder={replyTo ? "Trả lời bình luận..." : "Viết bình luận..."}
                            value={inputValue}
                            onChangeText={setInputValue}
                        />
                        <TouchableOpacity onPress={handleSendComment} style={styles.sendButton} disabled={submitting}>
                            <Ionicons name="send" size={20} color="#fff" />
                        </TouchableOpacity>
                    </View>
                </View>
            </View>
        </Modal>
    );
};

const styles = StyleSheet.create({
    modalBackground: {
        flex: 1,
        justifyContent: 'flex-end',
        backgroundColor: 'rgba(0,0,0,0.3)',
    },
    modalContainer: {
        height: '65%',
        backgroundColor: '#fff',
        borderTopLeftRadius: 20,
        borderTopRightRadius: 20,
        padding: 16,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 10,
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
    },
    avatar: {
        width: 32,
        height: 32,
        borderRadius: 16,
        marginRight: 8,
    },
    commentBox: {
        backgroundColor: '#f0f0f0',
        padding: 10,
        borderRadius: 10,
        flex: 1,
    },
    username: {
        fontWeight: 'bold',
        marginBottom: 4,
    },
    inputContainer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        flexDirection: 'row',
        alignItems: 'center',
        padding: 10,
        backgroundColor: '#fff',
        borderTopWidth: 1,
        borderColor: '#ddd',
    },
    input: {
        flex: 1,
        borderWidth: 1,
        borderColor: '#ccc',
        borderRadius: 20,
        paddingHorizontal: 15,
        paddingVertical: 8,
        backgroundColor: '#f9f9f9',
    },
    sendButton: {
        backgroundColor: '#007bff',
        padding: 10,
        borderRadius: 20,
        marginLeft: 8,
    },
    actions: {
        flexDirection: 'row',
        marginTop: 6,
        gap: 16,
    },
    replyText: {
        color: '#007bff',
        fontSize: 13,
    }
});

export default CommentPostSection;

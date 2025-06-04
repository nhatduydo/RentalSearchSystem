import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const CommentSection = ({ roomId }) => {
  const comments = [
    {
      id: 1,
      user: 'Nguyễn Văn A',
      content: 'Phòng đẹp, yên tĩnh và giá hợp lý!',
    },
    {
      id: 2,
      user: 'Trần Thị B',
      content: 'Chủ trọ thân thiện, gần khu công nghiệp.',
    },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Bình luận</Text>
      {comments.map((comment) => (
        <View key={comment.id} style={styles.commentBox}>
          <Text style={styles.userName}>{comment.user}</Text>
          <Text>{comment.content}</Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 24,
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
  },
  commentBox: {
    padding: 10,
    backgroundColor: '#f5f5f5',
    marginBottom: 10,
    borderRadius: 6,
  },
  userName: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
});

export default CommentSection;

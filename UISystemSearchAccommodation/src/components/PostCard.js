import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import RenderHTML from 'react-native-render-html';
import dayjs from 'dayjs';
import { useWindowDimensions } from 'react-native';

const PostCard = ({ post }) => {
    const { width } = useWindowDimensions();

    return (
        <View style={styles.card}>
            <View style={styles.header}>
                <Image source={{ uri: post.user.avatar }} style={styles.avatar} />
                <View style={styles.userInfo}>
                    <Text style={styles.username}>{post.user.first_name} {post.user.last_name}</Text>
                    <Text style={styles.date}>
                        {dayjs(post.created_date).format('MMM D')}
                    </Text>
                </View>
                <TouchableOpacity style={styles.menuButton}>
                    <Icon name="dots-vertical" size={20} color="#555" />
                </TouchableOpacity>
            </View>

            <Text style={styles.title}>{post.title}</Text>

            <RenderHTML contentWidth={width} source={{ html: post.content }} baseStyle={styles.content} />

            {post.images.length > 0 && (
                <Image source={{ uri: post.images[0] }} style={styles.postImage} />
            )}

            <View style={styles.footer}>
                <View style={styles.footerItem}>
                    <Icon name="heart-outline" size={20} />
                    <Text style={styles.footerText}>0</Text>
                </View>
                <View style={styles.footerItem}>
                    <Icon name="comment-outline" size={20} />
                    <Text style={styles.footerText}>{post.comments_count}</Text>
                </View>
                <TouchableOpacity style={styles.footerItem}>
                    <Icon name="share-outline" size={20} />
                </TouchableOpacity>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    card: {
        margin: 10,
        backgroundColor: '#fff',
        borderRadius: 15,
        padding: 12,
        shadowColor: '#000',
        shadowOpacity: 0.05,
        shadowRadius: 10,
        elevation: 3,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 6,
    },
    avatar: {
        width: 38,
        height: 38,
        borderRadius: 19,
    },
    userInfo: {
        marginLeft: 10,
        flex: 1,
    },
    username: {
        fontWeight: 'bold',
        fontSize: 14,
    },
    date: {
        color: '#888',
        fontSize: 12,
    },
    menuButton: {
        paddingHorizontal: 4,
    },
    title: {
        fontSize: 15,
        fontWeight: '500',
        marginVertical: 6,
    },
    content: {
        fontSize: 14,
        color: '#333',
        marginBottom: 10,
    },
    postImage: {
        width: '100%',
        height: 200,
        borderRadius: 10,
        marginTop: 10,
    },
    footer: {
        marginTop: 10,
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingHorizontal: 10,
    },
    footerItem: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    footerText: {
        marginLeft: 4,
        fontSize: 13,
    },
});

export default PostCard;

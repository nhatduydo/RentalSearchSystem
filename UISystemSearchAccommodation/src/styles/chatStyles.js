import { Platform, StatusBar, StyleSheet } from 'react-native';

export const chatStyles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f1f1f1',
    },

    header: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#2196F3',
        paddingHorizontal: 15,
        paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 44,
        paddingBottom: 12,
    },
    avatar: {
        width: 36,
        height: 36,
        borderRadius: 18,
        marginHorizontal: 10,
    },
    name: {
        color: '#fff',
        fontSize: 18,
        fontWeight: '500',
    },

    messageContainer: {
        maxWidth: '75%',
        borderRadius: 10,
        padding: 10,
        marginVertical: 5,
    },
    myMessage: {
        alignSelf: 'flex-end',
        backgroundColor: '#DCF8C6',
    },
    otherMessage: {
        alignSelf: 'flex-start',
        backgroundColor: '#fff',
    },
    messageText: {
        fontSize: 15,
    },
    inputContainer: {
        flexDirection: 'row',
        padding: 10,
        borderTopWidth: 1,
        borderColor: '#ccc',
        backgroundColor: '#fff',
    },
    input: {
        flex: 1,
        backgroundColor: '#eee',
        borderRadius: 20,
        paddingHorizontal: 15,
        paddingVertical: 8,
        marginRight: 10,
    },
});

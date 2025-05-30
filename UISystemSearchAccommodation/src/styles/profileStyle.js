import { StyleSheet } from "react-native";

const profileStyle = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        paddingHorizontal: 24,
        alignItems: 'center',
        justifyContent: 'center',
    },
    image: {
        width: 250,
        height: 250,
        marginBottom: 20,
    },
    title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 4,
        color: '#000',
    },
    subtitle: {
        fontSize: 28,
        fontWeight: 'bold',
        marginBottom: 12,
        color: 'deepskyblue',
    },
    description: {
        textAlign: 'center',
        fontSize: 14,
        color: '#666',
        marginBottom: 30,
        paddingHorizontal: 10,
    },
    loginButton: {
        backgroundColor: 'deepskyblue',
        borderRadius: 12,
        width: '100%',
        paddingVertical: 14,
        marginBottom: 10,
    },
    loginText: {
        color: '#000',
        fontWeight: 'bold',
        textAlign: 'center',
        fontSize: 16,
    },
    registerButton: {
        backgroundColor: '#ccc',
        borderRadius: 12,
        width: '100%',
        paddingVertical: 14,
    },
    registerText: {
        color: '#000',
        fontWeight: 'bold',
        textAlign: 'center',
        fontSize: 16,
    },
});

export default profileStyle;

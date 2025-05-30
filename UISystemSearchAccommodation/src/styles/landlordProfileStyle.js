import { StyleSheet } from 'react-native';

export default StyleSheet.create({
    landlordContainer: {
        flex: 1,
        backgroundColor: '#fff',
    },
    landlordProfileHeader: {
        backgroundColor: '#008b8b',
        paddingBottom: 20,
        width: '100%',
    },

    landlordProfileTopBar: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 20,
        paddingTop: 50,
    },

    landlordProfileInfo: {
        alignItems: 'center',
        paddingTop: 10,
    },

    landlordAvatar: {
        width: 90,
        height: 90,
        borderRadius: 45,
        borderWidth: 2,
        borderColor: '#fff',
        marginBottom: 10,
    },

    landlordName: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#fff',
    },

    landlordEmail: {
        color: '#f0f0f0',
        marginTop: 4,
    },

    landlordStatsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        width: '60%',
        marginTop: 15,
    },

    landlordStatBox: {
        alignItems: 'center',
    },

    landlordStatValue: {
        fontWeight: 'bold',
        fontSize: 16,
        color: '#fff',
    },

    landlordStatLabel: {
        color: '#f0f0f0',
        fontSize: 12,
    },

    landlordHeaderContainer: {
        backgroundColor: '#009999',
        borderBottomLeftRadius: 20,
        borderBottomRightRadius: 20,
        paddingBottom: 60,
        width: '100%',
    },

    landlordHeaderTopRow: {
        flexDirection: 'row',
        justifyContent: 'flex-end',
        alignItems: 'center',
        padding: 16,
        paddingTop: 50,
    },

    landlordAvatarSection: {
        alignItems: 'center',
        marginTop: -40,
    },

    landlordAvatarLarge: {
        width: 120,
        height: 120,
        borderRadius: 60,
        borderWidth: 2,
        borderColor: '#ccc',
    },

    landlordVerified: {
        color: '#4CAF50',
        fontWeight: 'bold',
        marginTop: 4,
    },

    landlordRole: {
        fontSize: 14,
        fontStyle: 'italic',
        color: '#ffcc00',
        marginVertical: 4,
    },

    landlordAddress: {
        color: '#e0e0e0',
        textAlign: 'center',
        marginTop: 4,
    },

    horizontalScrollContainer: {
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 12,
        paddingVertical: 10,
    },

    landlordInfoBox: {
        
        width: '90%',
        backgroundColor: '#f9f9f9',
        padding: 15,
        borderRadius: 10,
        marginVertical: 10,
        marginHorizontal: 20,
        elevation: 1,
    },

    landlordSectionTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 10,
    },

    landlordLink: {
        color: '#1e90ff',
        marginTop: 10,
    },

    landlordFooterLinks: {
        marginBottom: 30,
        alignItems: 'center',
    },
});

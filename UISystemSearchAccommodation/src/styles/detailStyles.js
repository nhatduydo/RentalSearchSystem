import { StyleSheet, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');

const detailStyles = StyleSheet.create({
    container: {
        padding: 16,
        backgroundColor: '#fff',
    },
    price: { fontSize: 20, color: 'red', marginVertical: 5, fontWeight: 'bold' },
    button: {
        backgroundColor: '#007AFF',
        padding: 12,
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },

    buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    title: {
        fontSize: 22,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    description: {
        fontSize: 16,
        fontStyle: 'italic',
        marginBottom: 12,
    },
    infoBlock1: {
        marginBottom: 8,
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    infoBlock2: {
        marginBottom: 8,
    },
    section: {
        marginBottom: 20,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        marginBottom: 8,
    },
    amenitiesContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
    },
    amenityItem: {
        marginRight: 12,
        marginBottom: 6,
    },
    amenityText: {
        fontSize: 14,
        color: '#444',
    },
    scrollView: {
        height: 200,
    },
    carouselImage: {
        width: Dimensions.get('window').width,
        height: 200,
        resizeMode: 'cover',
        margin: 0,
        padding: 0,
    },

});

export default detailStyles;

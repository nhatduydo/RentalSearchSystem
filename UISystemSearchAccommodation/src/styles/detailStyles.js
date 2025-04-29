import { StyleSheet, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');

const detailStyles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
    image: { width: width, height: 200 },
    info: { padding: 16 },
    title: { fontSize: 18, fontWeight: 'bold' },
    price: { fontSize: 16, color: 'red', marginVertical: 5 },
    location: { fontSize: 14, marginBottom: 4 },
    details: { fontSize: 14, marginBottom: 4 },
    total: { fontSize: 14, color: 'gray' },
    sectionTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        marginTop: 16,
        marginBottom: 8,
    },
    expenseText: {
        fontSize: 14,
        marginBottom: 4,
    },
    scrollView: {
        backgroundColor: '#fff',
        width: width,
    },
    carouselImage: {
        width: width,
        height: 300,
    },
    button: {
        flex: 1,
        backgroundColor: '#007AFF',
        padding: 12,
        borderRadius: 8,
        alignItems: 'center',
    },
    buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
    costGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        marginTop: 8,
    },

    costCell: {
        width: '33.33%',
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 8,
        alignItems: 'center',
        justifyContent: 'center',
    },

    costLabel: {
        fontSize: 14,
        fontWeight: 'bold',
    },

    costValue: {
        fontSize: 14,
        color: 'blue',
        marginVertical: 2,
    },

    costUnit: {
        fontSize: 12,
        color: '#555',
    },

});

export default detailStyles;

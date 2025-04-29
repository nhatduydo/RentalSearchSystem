import { StyleSheet } from 'react-native';
const filterStyles = StyleSheet.create({
    container: { padding: 16, backgroundColor: '#fff' },
    header: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
    pickerWrapper: { marginBottom: 16 },
    label: { marginBottom: 6, fontSize: 14 },
    picker: { backgroundColor: '#f2f2f2', borderRadius: 8 },
    sectionTitle: { fontWeight: 'bold', marginTop: 20, marginBottom: 8 },
    optionContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
    optionButton: {
      paddingHorizontal: 16,
      paddingVertical: 10,
      borderRadius: 20,
      backgroundColor: '#eee',
      marginBottom: 8,
    },
    optionButtonSelected: { backgroundColor: '#1976D2' },
    optionText: { color: '#333' },
    optionTextSelected: { color: '#fff', fontWeight: 'bold' },
    applyButton: {
      backgroundColor: '#1976D2',
      paddingVertical: 14,
      borderRadius: 24,
      alignItems: 'center',
      marginTop: 30,
    },
    applyButtonText: { color: 'white', fontSize: 16, fontWeight: '600' },
  });

  export default filterStyles;
  
import { StyleSheet } from 'react-native';

export const NotificationStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    backgroundColor: '#2196F3',
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
    alignItems: 'center'
  },
  headerText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
  },
  searchBar: {
    width: '100%',
    marginHorizontal: 20,
    backgroundColor: '#fff',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    elevation: 3,
  },
  itemContainer: {
    flexDirection: 'row',
    padding: 15,
    borderBottomWidth: 0.5,
    borderColor: '#ccc',
  },
  logo: {
    width: 40,
    height: 40,
    marginRight: 10,
  },
  textWrapper: {
    flex: 1,
  },
  title: {
    fontWeight: 'bold',
    fontSize: 15,
    marginBottom: 4,
  },
  description: {
    color: '#555',
    fontSize: 14,
  },
  meta: {
    fontSize: 12,
    color: '#888',
    marginTop: 2,
  },

});

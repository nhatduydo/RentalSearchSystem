import { StyleSheet } from "react-native";

const registerStyles = StyleSheet.create({
    container: {
      flex: 1,
      padding: 20,
      backgroundColor: 'lightblue',
      justifyContent: 'center',
    },
    title: {
      color: 'white',
      fontSize: 28,
      fontWeight: 'bold',
      marginBottom: 30,
    },
    form: {
      backgroundColor: 'white',
      borderRadius: 20,
      padding: 20,
    },
    input: {
      borderBottomWidth: 1,
      borderColor: '#ccc',
      marginBottom: 20,
      paddingVertical: 8,
      paddingHorizontal: 10,
      fontSize: 16,
    },
    signUpBtn: {
      backgroundColor: '#00aaff',
      paddingVertical: 12,
      borderRadius: 10,
      alignItems: 'center',
      marginTop: 10,
    },
    signUpText: {
      color: 'white',
      fontSize: 16,
    },
    haveAccount: {
      marginTop: 15,
      textAlign: 'center',
      fontSize: 14,
    },
    loginLink: {
      color: 'green',
      fontWeight: 'bold',
    },
  });

  export default registerStyles;
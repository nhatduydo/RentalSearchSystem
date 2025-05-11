import { StyleSheet } from "react-native";

const loginStyles = StyleSheet.create({
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
  forgot: {
    color: 'orange',
    textAlign: 'right',
    marginBottom: 20,
  },
  signInBtn: {
    backgroundColor: '#00aaff',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 20,
  },
  signInText: {
    color: 'white',
    fontSize: 16,
  },
  orText: {
    textAlign: 'center',
    marginVertical: 10,
    color: '#666',
  },
  socialRow: {
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'center',
    marginBottom: 20,
  },
  fbBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#3b5998',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  googleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#db4437',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  fbText: {
    color: 'white',
    fontWeight: 'bold',
  },
  googleText: {
    color: 'white',
    fontWeight: 'bold',
  },
  terms: {
    fontSize: 12,
    textAlign: 'center',
    color: '#666',
  },
  termsLink: {
    color: 'green',
  },
  signupText: {
    marginTop: 10,
    fontSize: 14,
    textAlign: 'center',
  },
  signupLink: {
    color: 'green',
    fontWeight: 'bold',
  },
});

export default loginStyles;
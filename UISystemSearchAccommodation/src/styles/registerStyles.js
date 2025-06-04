import { StyleSheet } from "react-native";

const registerStyles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: 'lightblue',
    justifyContent: 'center',
  },
  title: {
    color: 'deepblue',
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 30,
  },
  form: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 15,
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
  roleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginVertical: 15,
  },

  roleLabel: {
    fontSize: 16,
    fontWeight: '600',
  },

  roleSwitchWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },

  roleOption: {
    fontSize: 14,
    color: '#555',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ccc',
    marginRight: 10,
  },

  selectedRole: {
    backgroundColor: '#00aaff',
    color: 'white',
    borderColor: '#00aaff',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  halfInput: {
  flex: 1,
}


});

export default registerStyles;
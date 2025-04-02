// src/screens/auth/LoginScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { theme } from '../../theme';
import { RootStackParamList } from '../../types/navigation';

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Login'>;

interface LoginScreenProps {
  navigation: LoginScreenNavigationProp;
}

const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const { signIn } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({});

  const validate = () => {
    const newErrors: { username?: string; password?: string } = {};
    if (!username) newErrors.username = 'Username is required';
    if (!password) newErrors.password = 'Password is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validate()) return;

    setIsLoading(true);
    try {
      await signIn(username, password);
    } catch (error) {
      // Handle different error types
      if (axios.isAxiosError(error) && error.response) {
        // Handle API errors
        if (error.response.status === 401) {
          Alert.alert('Login Failed', 'Invalid username or password');
        } else {
          Alert.alert('Error', 'An error occurred while logging in');
        }
      } else {
        Alert.alert('Error', 'Could not connect to the server');
      }
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Text style={styles.title}>Welcome Back</Text>
          <Text style={styles.subtitle}>Sign in to access your gift cards</Text>
        </View>

        <View style={styles.form}>
          <Input
            label="Username"
            value={username}
            onChangeText={setUsername}
            placeholder="Enter your username"
            error={errors.username}
            autoCapitalize="none"
          />

          <Input
            label="Password"
            value={password}
            onChangeText={setPassword}
            placeholder="Enter your password"
            secureTextEntry
            error={errors.password}
          />

          <Button
            title={isLoading ? 'Signing In...' : 'Sign In'}
            onPress={handleLogin}
            disabled={isLoading}
            style={styles.button}
          />

          {isLoading && (
            <ActivityIndicator
              size="large"
              color={theme.colors.primary}
              style={styles.loader}
            />
          )}
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Don't have an account?</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Register')}>
            <Text style={styles.registerLink}>Sign Up</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  scrollContainer: {
    flexGrow: 1,
    padding: theme.spacing.lg,
  },
  header: {
    marginBottom: theme.spacing.xl,
    alignItems: 'center',
  },
  title: {
    ...theme.typography.h1,
    marginBottom: theme.spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.gray,
    textAlign: 'center',
  },
  form: {
    marginBottom: theme.spacing.xl,
  },
  button: {
    marginTop: theme.spacing.md,
  },
  loader: {
    marginTop: theme.spacing.md,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 'auto',
    padding: theme.spacing.md,
  },
  footerText: {
    color: theme.colors.gray,
    marginRight: theme.spacing.xs,
  },
  registerLink: {
    color: theme.colors.primary,
    fontWeight: 'bold',
  },
});

export default LoginScreen;
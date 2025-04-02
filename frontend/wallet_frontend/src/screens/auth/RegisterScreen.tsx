// src/screens/auth/RegisterScreen.tsx
import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Formik } from 'formik';
import * as Yup from 'yup';
import DateTimePicker from '@react-native-community/datetimepicker';
import axios from 'axios';

import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { theme } from '../../theme';
import { RootStackParamList } from '../../types/navigation';

type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Register'>;

interface RegisterScreenProps {
  navigation: RegisterScreenNavigationProp;
}

// Validation schema
const RegisterSchema = Yup.object().shape({
  username: Yup.string()
    .min(3, 'Username must be at least 3 characters')
    .required('Username is required'),
  password: Yup.string()
    .min(8, 'Password must be at least 8 characters')
    .matches(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .matches(/[a-z]/, 'Password must contain at least one lowercase letter')
    .matches(/[0-9]/, 'Password must contain at least one number')
    .required('Password is required'),
  confirmPassword: Yup.string()
    .oneOf([Yup.ref('password'), null], 'Passwords must match')
    .required('Confirm password is required'),
  email: Yup.string()
    .email('Invalid email address')
    .required('Email is required'),
  first_name: Yup.string()
    .required('First name is required'),
  last_name: Yup.string()
    .required('Last name is required'),
  date_of_birth: Yup.date()
    .max(new Date(), 'Date of birth cannot be in the future')
    .required('Date of birth is required'),
});

const RegisterScreen: React.FC<RegisterScreenProps> = ({ navigation }) => {
  const { signUp } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  const handleRegister = async (values: any) => {
    setIsLoading(true);
    try {
      // Format date of birth as YYYY-MM-DD
      const date = values.date_of_birth;
      const formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      
      const userData = {
        ...values,
        date_of_birth: formattedDate,
      };
      
      delete userData.confirmPassword; // Remove confirmPassword as it's not needed for API
      
      await signUp(userData);
      // Navigation to home is handled by the auth context after successful signup
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        // Handle API errors
        const status = error.response.status;
        const errorData = error.response.data;
        
        if (status === 400 && errorData.detail) {
          Alert.alert('Registration Failed', errorData.detail);
        } else {
          Alert.alert('Registration Failed', 'An error occurred during registration');
        }
      } else {
        Alert.alert('Error', 'Could not connect to the server');
      }
      console.error('Registration error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Sign up to get started</Text>
        </View>

        <Formik
          initialValues={{
            username: '',
            password: '',
            confirmPassword: '',
            email: '',
            first_name: '',
            last_name: '',
            date_of_birth: new Date(2000, 0, 1), // Default to January 1, 2000
          }}
          validationSchema={RegisterSchema}
          onSubmit={handleRegister}
        >
          {({ handleChange, handleBlur, handleSubmit, values, errors, touched, setFieldValue }) => (
            <View style={styles.form}>
              <Input
                label="Username"
                value={values.username}
                onChangeText={handleChange('username')}
                onBlur={handleBlur('username')}
                placeholder="Enter your username"
                error={touched.username && errors.username}
                autoCapitalize="none"
              />

              <Input
                label="Email"
                value={values.email}
                onChangeText={handleChange('email')}
                onBlur={handleBlur('email')}
                placeholder="Enter your email"
                keyboardType="email-address"
                error={touched.email && errors.email}
              />

              <Input
                label="First Name"
                value={values.first_name}
                onChangeText={handleChange('first_name')}
                onBlur={handleBlur('first_name')}
                placeholder="Enter your first name"
                autoCapitalize="words"
                error={touched.first_name && errors.first_name}
              />

              <Input
                label="Last Name"
                value={values.last_name}
                onChangeText={handleChange('last_name')}
                onBlur={handleBlur('last_name')}
                placeholder="Enter your last name"
                autoCapitalize="words"
                error={touched.last_name && errors.last_name}
              />

              <View style={styles.dateContainer}>
                <Text style={styles.label}>Date of Birth</Text>
                <TouchableOpacity 
                  style={styles.dateButton}
                  onPress={() => setShowDatePicker(true)}
                >
                  <Text style={styles.dateText}>
                    {values.date_of_birth.toLocaleDateString()}
                  </Text>
                </TouchableOpacity>
                {touched.date_of_birth && errors.date_of_birth && (
                  <Text style={styles.errorText}>{errors.date_of_birth}</Text>
                )}
                
                {showDatePicker && (
                  <DateTimePicker
                    value={values.date_of_birth}
                    mode="date"
                    display="default"
                    onChange={(event, selectedDate) => {
                      setShowDatePicker(false);
                      if (selectedDate) {
                        setFieldValue('date_of_birth', selectedDate);
                      }
                    }}
                    maximumDate={new Date()}
                  />
                )}
              </View>

              <Input
                label="Password"
                value={values.password}
                onChangeText={handleChange('password')}
                onBlur={handleBlur('password')}
                placeholder="Enter your password"
                secureTextEntry
                error={touched.password && errors.password}
              />

              <Input
                label="Confirm Password"
                value={values.confirmPassword}
                onChangeText={handleChange('confirmPassword')}
                onBlur={handleBlur('confirmPassword')}
                placeholder="Confirm your password"
                secureTextEntry
                error={touched.confirmPassword && errors.confirmPassword}
              />

              <Button
                title={isLoading ? 'Creating Account...' : 'Create Account'}
                onPress={handleSubmit}
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
          )}
        </Formik>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account?</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Login')}>
            <Text style={styles.loginLink}>Sign In</Text>
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
  dateContainer: {
    marginBottom: theme.spacing.md,
    width: '100%',
  },
  label: {
    fontSize: 16,
    marginBottom: theme.spacing.xs,
    color: theme.colors.text,
  },
  dateButton: {
    borderWidth: 1,
    borderColor: theme.colors.gray,
    borderRadius: 8,
    padding: theme.spacing.md,
    backgroundColor: 'white',
  },
  dateText: {
    fontSize: 16,
  },
  errorText: {
    color: theme.colors.error,
    fontSize: 14,
    marginTop: theme.spacing.xs,
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
  loginLink: {
    color: theme.colors.primary,
    fontWeight: 'bold',
  },
});

export default RegisterScreen;
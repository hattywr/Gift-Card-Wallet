// src/navigation/AppNavigator.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Screens
import HomeScreen from '../screens/HomeScreen';
import ProfileScreen from '../screens/ProfileScreen';
import SettingsScreen from '../screens/SettingsScreen';
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import AddGiftCardScreen from '../screens/AddGiftCardScreen';
import GiftCardDetailScreen from '../screens/GiftCardDetailScreen';

// Context
import { useAuth } from '../context/AuthContext';

// Types
import { RootStackParamList } from '../types/navigation';
import { theme } from '../theme';

const Stack = createNativeStackNavigator<RootStackParamList>();

export const AppNavigator: React.FC = () => {
  const { isSignedIn, isLoading, signOut } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: theme.colors.background,
          },
          headerTintColor: theme.colors.text,
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        }}
      >
        {isSignedIn ? (
          // Main App Screens
          <>
            <Stack.Screen 
              name="Home" 
              component={HomeScreen}
              options={{
                title: 'Gift Card Wallet',
                headerRight: () => (
                  <Icon
                    name="logout"
                    size={24}
                    color={theme.colors.primary}
                    style={{ marginRight: 10 }}
                    onPress={() => signOut()}
                  />
                ),
              }}
            />
            <Stack.Screen 
              name="Profile" 
              component={ProfileScreen}
              options={{ title: 'My Profile' }}
            />
            <Stack.Screen 
              name="Settings" 
              component={SettingsScreen}
              options={{ title: 'Settings' }}
            />
            <Stack.Screen 
              name="AddGiftCard" 
              component={AddGiftCardScreen}
              options={{ title: 'Add Gift Card' }}
            />
            <Stack.Screen 
              name="GiftCardDetail" 
              component={GiftCardDetailScreen}
              options={{ title: 'Gift Card Details' }}
            />
          </>
        ) : (
          // Auth Screens
          <>
            <Stack.Screen 
              name="Login" 
              component={LoginScreen}
              options={{ headerShown: false }}
            />
            <Stack.Screen 
              name="Register" 
              component={RegisterScreen}
              options={{ headerShown: false }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
});
// App.tsx
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppNavigator } from './src/navigation/AppNavigator';
import { AuthProvider } from './src/context/AuthContext';
import FlashMessage from 'react-native-flash-message';

const App: React.FC = () => {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <AppNavigator />
        <FlashMessage position="top" />
      </AuthProvider>
    </SafeAreaProvider>
  );
};

export default App;
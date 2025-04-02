// src/components/common/Input.tsx
import React from 'react';
import { TextInput, View, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { theme } from '../../theme';

interface InputProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  label?: string;
  error?: string;
  style?: ViewStyle;
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  keyboardType?: 'default' | 'email-address' | 'numeric' | 'phone-pad';
}

export const Input: React.FC<InputProps> = ({
  value,
  onChangeText,
  placeholder,
  secureTextEntry = false,
  label,
  error,
  style,
  autoCapitalize = 'none',
  keyboardType = 'default',
}) => {
  return (
    <View style={[styles.container, style]}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TextInput
        style={[styles.input, error ? styles.inputError : null]}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        secureTextEntry={secureTextEntry}
        autoCapitalize={autoCapitalize}
        keyboardType={keyboardType}
      />
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
};

interface Styles {
  container: ViewStyle;
  label: TextStyle;
  input: ViewStyle & TextStyle;
  inputError: ViewStyle;
  errorText: TextStyle;
}

const styles = StyleSheet.create<Styles>({
  container: {
    marginBottom: theme.spacing.md,
    width: '100%',
  },
  label: {
    fontSize: 16,
    marginBottom: theme.spacing.xs,
    color: theme.colors.text,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.gray,
    borderRadius: 8,
    padding: theme.spacing.md,
    fontSize: 16,
    backgroundColor: 'white',
  },
  inputError: {
    borderColor: theme.colors.error,
  },
  errorText: {
    color: theme.colors.error,
    fontSize: 14,
    marginTop: theme.spacing.xs,
  },
});
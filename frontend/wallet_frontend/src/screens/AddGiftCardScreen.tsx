// src/screens/AddGiftCardScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
  TextInput,
  Platform
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Picker } from '@react-native-picker/picker';
import DateTimePicker from '@react-native-community/datetimepicker';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card } from '../components/common/Card';
import { theme } from '../theme';
import { RootStackParamList } from '../types/navigation';
import { useAuth } from '../context/AuthContext';
import { giftCardService, vendorService } from '../services/api';

type AddGiftCardScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'AddGiftCard'
>;

interface AddGiftCardScreenProps {
  navigation: AddGiftCardScreenNavigationProp;
}

interface Vendor {
  vendor_id: string;
  company_name: string;
}

const AddGiftCardScreen: React.FC<AddGiftCardScreenProps> = ({ navigation }) => {
  const { user } = useAuth();
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [isLoadingVendors, setIsLoadingVendors] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Form state
  const [selectedVendor, setSelectedVendor] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [pin, setPin] = useState('');
  const [balance, setBalance] = useState('');
  const [expirationDate, setExpirationDate] = useState<Date | null>(null);
  const [frontImage, setFrontImage] = useState<any>(null);
  const [backImage, setBackImage] = useState<any>(null);
  
  // UI state
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  
  useEffect(() => {
    const fetchVendors = async () => {
      try {
        setIsLoadingVendors(true);
        const response = await vendorService.getAllVendors();
        setVendors(response);
      } catch (error) {
        console.error('Error fetching vendors:', error);
        Alert.alert('Error', 'Failed to load vendors');
      } finally {
        setIsLoadingVendors(false);
      }
    };
    
    fetchVendors();
  }, []);
  
  const validate = () => {
    const newErrors: {[key: string]: string} = {};
    
    if (!selectedVendor) newErrors.vendor = 'Please select a vendor';
    if (!cardNumber) newErrors.cardNumber = 'Card number is required';
    if (!balance) {
      newErrors.balance = 'Balance is required';
    } else if (isNaN(Number(balance)) || Number(balance) <= 0) {
      newErrors.balance = 'Please enter a valid balance';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleDateChange = (event: any, selectedDate?: Date) => {
    setShowDatePicker(false);
    if (selectedDate) {
      setExpirationDate(selectedDate);
    }
  };
  
  const pickImage = async (type: 'front' | 'back') => {
    try {
      const result = await launchImageLibrary({
        mediaType: 'photo',
        quality: 0.8,
      });
      
      if (result.assets && result.assets.length > 0) {
        const selectedImage = {
          uri: result.assets[0].uri,
          type: result.assets[0].type,
          name: result.assets[0].fileName,
        };
        
        if (type === 'front') {
          setFrontImage(selectedImage);
        } else {
          setBackImage(selectedImage);
        }
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to select image');
    }
  };
  
  const takePhoto = async (type: 'front' | 'back') => {
    try {
      const result = await launchCamera({
        mediaType: 'photo',
        quality: 0.8,
      });
      
      if (result.assets && result.assets.length > 0) {
        const selectedImage = {
          uri: result.assets[0].uri,
          type: result.assets[0].type,
          name: result.assets[0].fileName,
        };
        
        if (type === 'front') {
          setFrontImage(selectedImage);
        } else {
          setBackImage(selectedImage);
        }
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo');
    }
  };
  
  const handleSubmit = async () => {
    if (!validate()) return;
    
    try {
      setIsSubmitting(true);
      
      // Create form data
      const formData = new FormData();
      formData.append('user_id', user?.user_id || '');
      formData.append('vendor_id', selectedVendor);
      formData.append('card_number', cardNumber);
      if (pin) formData.append('pin', pin);
      formData.append('balance', balance);
      
      if (expirationDate) {
        // Format date as YYYY-MM-DD
        const formattedDate = expirationDate.toISOString().split('T')[0];
        formData.append('expiration_date', formattedDate);
      }
      
      if (frontImage) {
        formData.append('front_image', frontImage);
      }
      
      if (backImage) {
        formData.append('back_image', backImage);
      }
      
      // Call API
      await giftCardService.createGiftCard(formData);
      
      Alert.alert(
        'Success',
        'Gift card added successfully',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack()
          }
        ]
      );
    } catch (error) {
      console.error('Error adding gift card:', error);
      Alert.alert('Error', 'Failed to add gift card');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const renderImagePicker = (type: 'front' | 'back') => {
    const image = type === 'front' ? frontImage : backImage;
    
    return (
      <View style={styles.imagePickerContainer}>
        <Text style={styles.imagePickerLabel}>
          {type === 'front' ? 'Front Image' : 'Back Image'} (Optional)
        </Text>
        
        {image ? (
          <View style={styles.selectedImageContainer}>
            <Image source={{ uri: image.uri }} style={styles.selectedImage} />
            <TouchableOpacity
              style={styles.removeImageButton}
              onPress={() => type === 'front' ? setFrontImage(null) : setBackImage(null)}
            >
              <Icon name="close" size={20} color="white" />
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.imagePickerButtons}>
            <TouchableOpacity 
              style={styles.imagePickerButton}
              onPress={() => pickImage(type)}
            >
              <Icon name="photo-library" size={24} color={theme.colors.primary} />
              <Text style={styles.imagePickerButtonText}>Library</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={styles.imagePickerButton}
              onPress={() => takePhoto(type)}
            >
              <Icon name="camera-alt" size={24} color={theme.colors.primary} />
              <Text style={styles.imagePickerButtonText}>Camera</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container} edges={['left', 'right']}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.title}>Add Gift Card</Text>
        
        <Card style={styles.formCard}>
          {isLoadingVendors ? (
            <ActivityIndicator size="small" color={theme.colors.primary} />
          ) : (
            <View style={styles.pickerContainer}>
              <Text style={styles.label}>Vendor</Text>
              <View style={[
                styles.pickerWrapper, 
                errors.vendor ? styles.pickerError : null
              ]}>
                <Picker
                  selectedValue={selectedVendor}
                  onValueChange={(itemValue) => setSelectedVendor(itemValue)}
                  style={styles.picker}
                >
                  <Picker.Item label="Select a vendor" value="" />
                  {vendors.map((vendor) => (
                    <Picker.Item
                      key={vendor.vendor_id}
                      label={vendor.company_name}
                      value={vendor.vendor_id}
                    />
                  ))}
                </Picker>
              </View>
              {errors.vendor && (
                <Text style={styles.errorText}>{errors.vendor}</Text>
              )}
            </View>
          )}
          
          <Input
            label="Card Number"
            value={cardNumber}
            onChangeText={setCardNumber}
            placeholder="Enter gift card number"
            error={errors.cardNumber}
          />
          
          <Input
            label="PIN (Optional)"
            value={pin}
            onChangeText={setPin}
            placeholder="Enter PIN if available"
          />
          
          <Input
            label="Balance"
            value={balance}
            onChangeText={setBalance}
            placeholder="Enter current balance"
            keyboardType="decimal-pad"
            error={errors.balance}
          />
          
          <View style={styles.datePickerContainer}>
            <Text style={styles.label}>Expiration Date (Optional)</Text>
            <TouchableOpacity
              style={styles.datePickerButton}
              onPress={() => setShowDatePicker(true)}
            >
              <Text style={styles.datePickerText}>
                {expirationDate
                  ? expirationDate.toLocaleDateString()
                  : 'Select expiration date'}
              </Text>
            </TouchableOpacity>
            
            {showDatePicker && (
              <DateTimePicker
                value={expirationDate || new Date()}
                mode="date"
                display="default"
                onChange={handleDateChange}
                minimumDate={new Date()}
              />
            )}
          </View>
          
          {renderImagePicker('front')}
          {renderImagePicker('back')}
          
          <Button
            title={isSubmitting ? 'Adding...' : 'Add Gift Card'}
            onPress={handleSubmit}
            disabled={isSubmitting}
            style={styles.submitButton}
          />
        </Card>
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
    padding: theme.spacing.md,
  },
  title: {
    ...theme.typography.h1,
    marginBottom: theme.spacing.lg,
    textAlign: 'center',
  },
  formCard: {
    paddingVertical: theme.spacing.lg,
  },
  label: {
    fontSize: 16,
    marginBottom: theme.spacing.xs,
    color: theme.colors.text,
  },
  pickerContainer: {
    marginBottom: theme.spacing.md,
  },
  pickerWrapper: {
    borderWidth: 1,
    borderColor: theme.colors.gray,
    borderRadius: 8,
    backgroundColor: 'white',
  },
  pickerError: {
    borderColor: theme.colors.error,
  },
  picker: {
    height: 50,
  },
  errorText: {
    color: theme.colors.error,
    fontSize: 14,
    marginTop: theme.spacing.xs,
  },
  datePickerContainer: {
    marginBottom: theme.spacing.md,
  },
  datePickerButton: {
    borderWidth: 1,
    borderColor: theme.colors.gray,
    borderRadius: 8,
    padding: theme.spacing.md,
    backgroundColor: 'white',
  },
  datePickerText: {
    fontSize: 16,
  },
  imagePickerContainer: {
    marginBottom: theme.spacing.md,
  },
  imagePickerLabel: {
    fontSize: 16,
    marginBottom: theme.spacing.xs,
    color: theme.colors.text,
  },
  imagePickerButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: theme.spacing.sm,
  },
  imagePickerButton: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: theme.spacing.md,
    borderWidth: 1,
    borderColor: theme.colors.gray,
    borderRadius: 8,
    backgroundColor: 'white',
    width: 120,
  },
  imagePickerButtonText: {
    marginTop: theme.spacing.xs,
    color: theme.colors.primary,
  },
  selectedImageContainer: {
    position: 'relative',
    marginTop: theme.spacing.sm,
    alignItems: 'center',
  },
  selectedImage: {
    width: 200,
    height: 120,
    resizeMode: 'contain',
    borderRadius: 8,
  },
  removeImageButton: {
    position: 'absolute',
    top: -10,
    right: -10,
    backgroundColor: theme.colors.error,
    borderRadius: 15,
    padding: 5,
  },
  submitButton: {
    marginTop: theme.spacing.lg,
  },
});

export default AddGiftCardScreen;
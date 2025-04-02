// src/screens/GiftCardDetailScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  TextInput,
  Modal,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { theme } from '../theme';
import { RootStackParamList } from '../types/navigation';
import { giftCardService, vendorService } from '../services/api';

type GiftCardDetailScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'GiftCardDetail'
>;

type GiftCardDetailScreenRouteProp = RouteProp<
  RootStackParamList,
  'GiftCardDetail'
>;

interface GiftCardDetailScreenProps {
  navigation: GiftCardDetailScreenNavigationProp;
  route: GiftCardDetailScreenRouteProp;
}

const GiftCardDetailScreen: React.FC<GiftCardDetailScreenProps> = ({
  navigation,
  route,
}) => {
  const { cardId } = route.params;
  const [giftCard, setGiftCard] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showEditBalance, setShowEditBalance] = useState(false);
  const [newBalance, setNewBalance] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [currentView, setCurrentView] = useState<'front' | 'back'>('front');
  
  useEffect(() => {
    const fetchGiftCard = async () => {
      try {
        setIsLoading(true);
        const card = await giftCardService.getGiftCard(cardId);
        setGiftCard(card);
        setNewBalance(card.balance.toString());
      } catch (error) {
        console.error('Error fetching gift card:', error);
        Alert.alert('Error', 'Failed to load gift card details');
        navigation.goBack();
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchGiftCard();
  }, [cardId, navigation]);
  
  const handleUpdateBalance = async () => {
    if (!newBalance || isNaN(Number(newBalance)) || Number(newBalance) < 0) {
      Alert.alert('Invalid Balance', 'Please enter a valid balance amount');
      return;
    }
    
    try {
      setIsUpdating(true);
      const updatedCard = await giftCardService.updateGiftCardBalance(
        cardId,
        Number(newBalance)
      );
      setGiftCard(updatedCard);
      setShowEditBalance(false);
      Alert.alert('Success', 'Gift card balance updated successfully');
    } catch (error) {
      console.error('Error updating balance:', error);
      Alert.alert('Error', 'Failed to update gift card balance');
    } finally {
      setIsUpdating(false);
    }
  };
  
  if (isLoading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </SafeAreaView>
    );
  }
  
  if (!giftCard) return null;
  
  const frontImageUrl = giftCard.has_front_image
    ? giftCardService.getGiftCardImage(cardId, 'front')
    : null;
    
  const backImageUrl = giftCard.has_back_image
    ? giftCardService.getGiftCardImage(cardId, 'back')
    : null;
    
  const logoUrl = vendorService.getVendorLogo(giftCard.vendor_id);
  
  return (
    <SafeAreaView style={styles.container} edges={['left', 'right']}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <Image
              source={{ uri: logoUrl }}
              style={styles.logo}
              defaultSource={require('../../assets/default-logo.png')}
            />
          </View>
          <Text style={styles.vendorName}>{giftCard.vendor_name}</Text>
        </View>
        
        <View style={styles.cardImageContainer}>
          {(giftCard.has_front_image || giftCard.has_back_image) ? (
            <>
              <Image
                source={{ 
                  uri: currentView === 'front' 
                    ? frontImageUrl 
                    : backImageUrl
                }}
                style={styles.cardImage}
                resizeMode="contain"
              />
              
              {giftCard.has_front_image && giftCard.has_back_image && (
                <View style={styles.flipButtonContainer}>
                  <TouchableOpacity
                    style={styles.flipButton}
                    onPress={() => 
                      setCurrentView(prev => prev === 'front' ? 'back' : 'front')
                    }
                  >
                    <Icon name="flip" size={24} color="white" />
                    <Text style={styles.flipText}>
                      Flip to {currentView === 'front' ? 'back' : 'front'}
                    </Text>
                  </TouchableOpacity>
                </View>
              )}
            </>
          ) : (
            <View style={styles.noImageContainer}>
              <Icon name="credit-card" size={80} color={theme.colors.gray} />
              <Text style={styles.noImageText}>No card image available</Text>
            </View>
          )}
        </View>
        
        <Card style={styles.detailsCard}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Card Number</Text>
            <Text style={styles.detailValue}>{giftCard.card_number}</Text>
          </View>
          
          {giftCard.pin && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>PIN</Text>
              <Text style={styles.detailValue}>{giftCard.pin}</Text>
            </View>
          )}
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Balance</Text>
            <View style={styles.balanceContainer}>
              <Text style={styles.balanceValue}>
                ${parseFloat(giftCard.balance).toFixed(2)}
              </Text>
              <TouchableOpacity
                style={styles.editButton}
                onPress={() => setShowEditBalance(true)}
              >
                <Icon name="edit" size={20} color={theme.colors.primary} />
              </TouchableOpacity>
            </View>
          </View>
          
          {giftCard.expiration_date && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Expires</Text>
              <Text style={styles.detailValue}>
                {new Date(giftCard.expiration_date).toLocaleDateString()}
              </Text>
            </View>
          )}
          
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Date Added</Text>
            <Text style={styles.detailValue}>
              {new Date(giftCard.created_at).toLocaleDateString()}
            </Text>
          </View>
        </Card>
      </ScrollView>
      
      {/* Edit Balance Modal */}
      <Modal
        visible={showEditBalance}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowEditBalance(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Update Balance</Text>
            
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>Current Balance: ${parseFloat(giftCard.balance).toFixed(2)}</Text>
              <TextInput
                style={styles.input}
                value={newBalance}
                onChangeText={setNewBalance}
                placeholder="Enter new balance"
                keyboardType="decimal-pad"
                autoFocus
              />
            </View>
            
            <View style={styles.modalButtonsContainer}>
              <Button
                title="Cancel"
                onPress={() => {
                  setNewBalance(giftCard.balance.toString());
                  setShowEditBalance(false);
                }}
                variant="secondary"
                style={styles.modalButton}
              />
              <Button
                title={isUpdating ? 'Updating...' : 'Update'}
                onPress={handleUpdateBalance}
                disabled={isUpdating}
                style={styles.modalButton}
              />
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
  scrollContainer: {
    padding: theme.spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  logoContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.spacing.md,
  },
  logo: {
    width: 35,
    height: 35,
    resizeMode: 'contain',
  },
  vendorName: {
    ...theme.typography.h2,
  },
  cardImageContainer: {
    height: 200,
    marginBottom: theme.spacing.lg,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f0f0f0',
    borderRadius: 10,
    overflow: 'hidden',
  },
  cardImage: {
    width: '100%',
    height: '100%',
  },
  flipButtonContainer: {
    position: 'absolute',
    bottom: theme.spacing.md,
    right: theme.spacing.md,
  },
  flipButton: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    padding: theme.spacing.sm,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  flipText: {
    color: 'white',
    marginLeft: theme.spacing.xs,
  },
  noImageContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  noImageText: {
    color: theme.colors.gray,
    marginTop: theme.spacing.sm,
  },
  detailsCard: {
    marginBottom: theme.spacing.lg,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  detailLabel: {
    fontSize: 16,
    color: theme.colors.gray,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '500',
  },
  balanceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  balanceValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.success,
    marginRight: theme.spacing.sm,
  },
  editButton: {
    padding: 4,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  modalContent: {
    width: '80%',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: theme.spacing.lg,
    alignItems: 'center',
  },
  modalTitle: {
    ...theme.typography.h2,
    marginBottom: theme.spacing.lg,
  },
  inputContainer: {
    width: '100%',
    marginBottom: theme.spacing.lg,
  },
  inputLabel: {
    fontSize: 16,
    marginBottom: theme.spacing.sm,
  },
  input: {
    borderWidth: 1,
    borderColor: theme.colors.gray,
    borderRadius: 8,
    padding: theme.spacing.md,
    fontSize: 18,
    width: '100%',
  },
  modalButtonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  modalButton: {
    flex: 1,
    marginHorizontal: theme.spacing.xs,
  },
});

export default GiftCardDetailScreen;
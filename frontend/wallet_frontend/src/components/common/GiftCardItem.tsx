// src/components/common/GiftCardItem.tsx
import React from 'react';
import { View, Text, Image, StyleSheet, TouchableOpacity, ImageBackground } from 'react-native';
import { theme } from '../../theme';
import { Card } from './Card';
import { vendorService } from '../../services/api';

interface GiftCardItemProps {
  card: {
    card_id: string;
    vendor_id: string;
    card_number: string;
    balance: number;
    vendor_name: string;
    has_front_image: boolean;
  };
  onPress: () => void;
}

export const GiftCardItem: React.FC<GiftCardItemProps> = ({ card, onPress }) => {
  const logoUrl = vendorService.getVendorLogo(card.vendor_id);
  
  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.8}>
      <Card style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.logoContainer}>
            <Image
              source={{ uri: logoUrl }}
              style={styles.logo}
              defaultSource={require('../../../assets/default-logo.png')}
            />
          </View>
          <Text style={styles.vendorName}>{card.vendor_name}</Text>
        </View>
        
        <View style={styles.cardContent}>
          <View style={styles.infoContainer}>
            <Text style={styles.cardNumber}>
              {card.card_number.slice(-4).padStart(card.card_number.length, '•')}
            </Text>
            <Text style={styles.balanceLabel}>Balance</Text>
            <Text style={styles.balance}>${parseFloat(card.balance.toString()).toFixed(2)}</Text>
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    marginHorizontal: theme.spacing.sm,
    marginVertical: theme.spacing.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  logoContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: theme.spacing.sm,
  },
  logo: {
    width: 30,
    height: 30,
    resizeMode: 'contain',
  },
  vendorName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: theme.colors.text,
  },
  cardContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoContainer: {
    flex: 1,
  },
  cardNumber: {
    fontSize: 16,
    color: theme.colors.gray,
    marginBottom: theme.spacing.xs,
  },
  balanceLabel: {
    fontSize: 14,
    color: theme.colors.gray,
    marginBottom: 2,
  },
  balance: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.success,
  },
});
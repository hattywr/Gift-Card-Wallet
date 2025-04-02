// src/screens/HomeScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '../components/common/Button';
import { GiftCardItem } from '../components/common/GiftCardItem';
import { theme } from '../theme';
import { RootStackParamList } from '../types/navigation';
import { useAuth } from '../context/AuthContext';
import { giftCardService } from '../services/api';

type HomeScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Home'>;

interface HomeScreenProps {
  navigation: HomeScreenNavigationProp;
}

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const { user } = useAuth();
  const [giftCards, setGiftCards] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  const fetchGiftCards = useCallback(async (page = 1, refresh = false) => {
    if (!user) return;
    
    try {
      if (refresh) {
        setIsRefreshing(true);
      } else if (page === 1) {
        setIsLoading(true);
      }
      
      const response = await giftCardService.getAllGiftCards(user.user_id, page);
      
      if (page === 1 || refresh) {
        setGiftCards(response.items);
      } else {
        setGiftCards(prev => [...prev, ...response.items]);
      }
      
      setCurrentPage(response.page);
      setTotalPages(response.pages);
    } catch (error) {
      console.error('Error fetching gift cards:', error);
      Alert.alert('Error', 'Failed to load gift cards');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [user]);
  
  // Fetch gift cards when the screen is focused
  useFocusEffect(
    useCallback(() => {
      fetchGiftCards(1, true);
    }, [fetchGiftCards])
  );
  
  const handleRefresh = () => {
    fetchGiftCards(1, true);
  };
  
  const handleLoadMore = () => {
    if (currentPage < totalPages && !isLoading) {
      fetchGiftCards(currentPage + 1);
    }
  };
  
  const handleCardPress = (cardId: string) => {
    navigation.navigate('GiftCardDetail', { cardId });
  };

  return (
    <SafeAreaView style={styles.container} edges={['left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.title}>My Gift Cards</Text>
        <Button 
          title="+ Add Card" 
          onPress={() => navigation.navigate('AddGiftCard')}
          variant="primary"
          style={styles.addButton}
        />
      </View>
      
      {isLoading && currentPage === 1 ? (
        <View style={styles.loaderContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
        </View>
      ) : giftCards.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>You don't have any gift cards yet.</Text>
          <Text style={styles.emptySubtext}>Add your first gift card to get started!</Text>
          <Button 
            title="Add Gift Card" 
            onPress={() => navigation.navigate('AddGiftCard')}
            style={styles.emptyButton}
          />
        </View>
      ) : (
        <FlatList
          data={giftCards}
          keyExtractor={(item) => item.card_id}
          renderItem={({ item }) => (
            <GiftCardItem 
              card={item} 
              onPress={() => handleCardPress(item.card_id)} 
            />
          )}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl 
              refreshing={isRefreshing} 
              onRefresh={handleRefresh} 
              colors={[theme.colors.primary]}
              tintColor={theme.colors.primary}
            />
          }
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.5}
          ListFooterComponent={
            currentPage < totalPages ? (
              <ActivityIndicator 
                size="small" 
                color={theme.colors.primary} 
                style={styles.footerLoader} 
              />
            ) : null
          }
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  title: {
    ...theme.typography.h2,
  },
  addButton: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
  },
  list: {
    padding: theme.spacing.sm,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  footerLoader: {
    marginVertical: theme.spacing.md,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  emptyText: {
    ...theme.typography.h2,
    textAlign: 'center',
    marginBottom: theme.spacing.sm,
  },
  emptySubtext: {
    fontSize: 16,
    color: theme.colors.gray,
    textAlign: 'center',
    marginBottom: theme.spacing.lg,
  },
  emptyButton: {
    width: '60%',
  },
});

export default HomeScreen;
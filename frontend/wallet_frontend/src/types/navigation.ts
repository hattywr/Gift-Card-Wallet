// src/types/navigation.ts
export type RootStackParamList = {
  // Auth Stack
  Login: undefined;
  Register: undefined;
  
  // Main Stack
  Home: undefined;
  AddGiftCard: undefined;
  GiftCardDetail: { cardId: string };
  Profile: undefined;
  Settings: undefined;
};
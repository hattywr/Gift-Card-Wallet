// src/utils/helpers.ts
export const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };
  
  export const capitalize = (str: string): string => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };
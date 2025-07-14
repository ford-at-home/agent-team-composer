import React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

// Wrapper component that ensures Tabs always render correctly
export const SafeTabs = ({ 
  defaultValue, 
  value, 
  onValueChange, 
  children, 
  className 
}: {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <Tabs 
      defaultValue={defaultValue} 
      value={value} 
      onValueChange={onValueChange}
      className={className}
    >
      {children}
    </Tabs>
  );
};

export { TabsList, TabsTrigger, TabsContent };
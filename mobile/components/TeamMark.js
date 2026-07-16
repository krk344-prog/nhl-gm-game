import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';

const FALLBACK_BG = '#242A33';
const FALLBACK_FG = '#F5F7FA';

function safeInitials(name, abbreviation) {
  const explicit = String(abbreviation || '').trim().toUpperCase().slice(0, 3);
  if (explicit) return explicit;

  return String(name || 'Team')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 3)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'TM';
}

/**
 * Reusable franchise identity mark for dense management surfaces.
 * Accepts only approved/local artwork. Missing assets degrade to legible initials.
 */
export default function TeamMark({
  name,
  abbreviation,
  logoSource = null,
  primaryColor = FALLBACK_BG,
  textColor = FALLBACK_FG,
  size = 36,
  variant = 'compact',
  testID,
}) {
  const initials = safeInitials(name, abbreviation);
  const label = `${name || 'Team'} crest`;
  const dimension = Math.max(24, Math.min(size, 72));

  return (
    <View
      accessible
      accessibilityRole="image"
      accessibilityLabel={label}
      testID={testID}
      style={[
        styles.frame,
        variant === 'hero' && styles.heroFrame,
        {
          width: dimension,
          height: dimension,
          borderRadius: dimension / 2,
          backgroundColor: primaryColor || FALLBACK_BG,
        },
      ]}
    >
      {logoSource ? (
        <Image
          accessibilityIgnoresInvertColors
          source={logoSource}
          resizeMode="contain"
          style={{ width: dimension * 0.72, height: dimension * 0.72 }}
        />
      ) : (
        <Text
          allowFontScaling
          maxFontSizeMultiplier={1.25}
          numberOfLines={1}
          style={[
            styles.initials,
            { color: textColor || FALLBACK_FG, fontSize: Math.max(10, dimension * 0.3) },
          ]}
        >
          {initials}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  frame: {
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.22)',
    overflow: 'hidden',
    flexShrink: 0,
  },
  heroFrame: {
    borderWidth: 2,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.32,
    shadowRadius: 12,
    elevation: 5,
  },
  initials: {
    fontWeight: '900',
    letterSpacing: 0.4,
    textAlign: 'center',
  },
});

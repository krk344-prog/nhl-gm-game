import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

const PALETTE = {
  surface: '#0D0F13',
  surfaceElevated: '#171A20',
  border: '#303640',
  text: '#F5F7FA',
  muted: '#9FA8B4',
  gold: '#D6A84B',
  goldSoft: '#4A3818',
  blocked: '#E7B85A',
};

/**
 * Reusable Stage 3 vertical slice for the approved roster-pack selector.
 * The component is intentionally data-driven and isolated from save creation.
 */
export default function RosterSourceCard({
  title,
  eyebrow,
  summary,
  consequences = [],
  selected = false,
  recommended = false,
  blockedReason = null,
  onPress,
  testID,
}) {
  const blocked = Boolean(blockedReason);
  const stateLabel = blocked ? 'Unavailable' : selected ? 'Selected' : recommended ? 'Recommended' : 'Available';
  const actionLabel = blocked ? 'Review blocker' : selected ? 'Selected' : 'Select roster source';

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${title}. ${stateLabel}. ${summary}`}
      accessibilityHint={blocked ? blockedReason : 'Selects this roster source for the new game setup.'}
      accessibilityState={{ disabled: blocked, selected }}
      disabled={blocked}
      onPress={onPress}
      testID={testID}
      style={({ pressed, focused }) => [
        styles.card,
        selected && styles.cardSelected,
        pressed && !blocked && styles.cardPressed,
        focused && styles.cardFocused,
        blocked && styles.cardBlocked,
      ]}
    >
      <View style={styles.topRow}>
        <View style={styles.headingWrap}>
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.title}>{title}</Text>
        </View>
        <View style={[styles.stateBadge, (selected || recommended) && styles.stateBadgeAccent]}>
          <Text style={[styles.stateText, (selected || recommended) && styles.stateTextAccent]}>
            {stateLabel}
          </Text>
        </View>
      </View>

      <Text style={styles.summary}>{summary}</Text>

      <View style={styles.consequenceList}>
        {consequences.slice(0, 3).map((item) => (
          <View key={item} style={styles.consequenceRow}>
            <Text accessibilityElementsHidden style={styles.consequenceIcon}>✓</Text>
            <Text style={styles.consequenceText}>{item}</Text>
          </View>
        ))}
      </View>

      {blocked ? (
        <View style={styles.blockedPanel} accessibilityRole="alert">
          <Text style={styles.blockedLabel}>BLOCKED</Text>
          <Text style={styles.blockedReason}>{blockedReason}</Text>
        </View>
      ) : null}

      <View style={styles.actionRow}>
        <Text style={[styles.actionText, blocked && styles.actionTextBlocked]}>{actionLabel}</Text>
        <Text accessibilityElementsHidden style={[styles.actionArrow, blocked && styles.actionTextBlocked]}>→</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: 292,
    minWidth: 252,
    flex: 1,
    padding: 20,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: PALETTE.border,
    backgroundColor: PALETTE.surface,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 18 },
    shadowOpacity: 0.4,
    shadowRadius: 24,
    elevation: 8,
  },
  cardSelected: {
    borderColor: PALETTE.gold,
    backgroundColor: PALETTE.surfaceElevated,
  },
  cardPressed: {
    opacity: 0.94,
  },
  cardFocused: {
    borderWidth: 2,
    borderColor: PALETTE.gold,
  },
  cardBlocked: {
    opacity: 0.82,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  headingWrap: {
    flex: 1,
  },
  eyebrow: {
    color: PALETTE.gold,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 1.4,
    marginBottom: 7,
  },
  title: {
    color: PALETTE.text,
    fontSize: 22,
    lineHeight: 27,
    fontWeight: '800',
  },
  stateBadge: {
    minHeight: 28,
    paddingHorizontal: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: PALETTE.border,
    justifyContent: 'center',
  },
  stateBadgeAccent: {
    borderColor: PALETTE.gold,
    backgroundColor: PALETTE.goldSoft,
  },
  stateText: {
    color: PALETTE.muted,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  stateTextAccent: {
    color: PALETTE.text,
  },
  summary: {
    color: PALETTE.muted,
    fontSize: 15,
    lineHeight: 22,
    marginTop: 14,
  },
  consequenceList: {
    marginTop: 18,
    gap: 10,
  },
  consequenceRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
  },
  consequenceIcon: {
    color: PALETTE.gold,
    fontSize: 14,
    fontWeight: '900',
    lineHeight: 20,
  },
  consequenceText: {
    color: PALETTE.text,
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  blockedPanel: {
    marginTop: 18,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: PALETTE.blocked,
    backgroundColor: '#251C0C',
  },
  blockedLabel: {
    color: PALETTE.blocked,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.1,
  },
  blockedReason: {
    color: PALETTE.text,
    fontSize: 13,
    lineHeight: 19,
    marginTop: 4,
  },
  actionRow: {
    minHeight: 44,
    marginTop: 'auto',
    paddingTop: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  actionText: {
    color: PALETTE.gold,
    fontSize: 14,
    fontWeight: '800',
  },
  actionArrow: {
    color: PALETTE.gold,
    fontSize: 20,
  },
  actionTextBlocked: {
    color: PALETTE.blocked,
  },
});

"use client";

import { motion, AnimatePresence, type Variants } from "framer-motion";
import React from "react";

// ============================================
// Spring Configurations (The "Attio Feel")
// ============================================
export const springConfig = {
    // Snappy - for hovers, small interactions
    snappy: { type: "spring", stiffness: 400, damping: 30 },
    // Smooth - for modals, panels
    smooth: { type: "spring", stiffness: 300, damping: 30 },
    // Bouncy - for playful elements
    bouncy: { type: "spring", stiffness: 500, damping: 25 },
    // Gentle - for large layout shifts
    gentle: { type: "spring", stiffness: 200, damping: 25 },
} as const;

// ============================================
// Fade In/Out
// ============================================
export const fadeVariants: Variants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
};

export const FadeIn = ({
    children,
    delay = 0,
    duration = 0.3,
    className,
}: {
    children: React.ReactNode;
    delay?: number;
    duration?: number;
    className?: string;
}) => (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration, delay }}
        className={className}
    >
        {children}
    </motion.div>
);

// ============================================
// Slide Up (for lists, cards appearing)
// ============================================
export const slideUpVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
};

export const SlideUp = ({
    children,
    delay = 0,
    className,
}: {
    children: React.ReactNode;
    delay?: number;
    className?: string;
}) => (
    <motion.div
        initial="hidden"
        animate="visible"
        exit="exit"
        variants={slideUpVariants}
        transition={{ ...springConfig.smooth, delay }}
        className={className}
    >
        {children}
    </motion.div>
);

// ============================================
// Scale In (for modals, popovers)
// ============================================
export const scaleInVariants: Variants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
};

export const ScaleIn = ({
    children,
    className,
}: {
    children: React.ReactNode;
    className?: string;
}) => (
    <motion.div
        initial="hidden"
        animate="visible"
        exit="exit"
        variants={scaleInVariants}
        transition={springConfig.snappy}
        className={className}
    >
        {children}
    </motion.div>
);

// ============================================
// Stagger Children (for lists)
// ============================================
export const staggerContainerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.05,
            delayChildren: 0.1,
        },
    },
};

export const staggerItemVariants: Variants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 },
};

export const StaggerContainer = ({
    children,
    className,
}: {
    children: React.ReactNode;
    className?: string;
}) => (
    <motion.div
        initial="hidden"
        animate="visible"
        variants={staggerContainerVariants}
        className={className}
    >
        {children}
    </motion.div>
);

export const StaggerItem = ({
    children,
    className,
}: {
    children: React.ReactNode;
    className?: string;
}) => (
    <motion.div
        variants={staggerItemVariants}
        transition={springConfig.smooth}
        className={className}
    >
        {children}
    </motion.div>
);

// ============================================
// Interactive Card (hover lift effect)
// ============================================
export const InteractiveCard = ({
    children,
    className,
    onClick,
}: {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
}) => (
    <motion.div
        className={className}
        whileHover={{
            scale: 1.02,
            y: -2,
            boxShadow: "0 10px 40px rgba(0, 0, 0, 0.12)"
        }}
        whileTap={{ scale: 0.98 }}
        transition={springConfig.snappy}
        onClick={onClick}
    >
        {children}
    </motion.div>
);

// ============================================
// Interactive Button (subtle press)
// ============================================
export const InteractiveButton = ({
    children,
    className,
    onClick,
    disabled,
}: {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
    disabled?: boolean;
}) => (
    <motion.button
        className={className}
        whileHover={!disabled ? { scale: 1.02 } : undefined}
        whileTap={!disabled ? { scale: 0.98 } : undefined}
        transition={springConfig.snappy}
        onClick={onClick}
        disabled={disabled}
    >
        {children}
    </motion.button>
);

// ============================================
// Layout Animation Wrapper
// ============================================
export const LayoutGroup = motion.div;

// ============================================
// Slide Panel (for sidebars)
// ============================================
export const slidePanelVariants: Variants = {
    hidden: { x: -300, opacity: 0 },
    visible: { x: 0, opacity: 1 },
    exit: { x: -300, opacity: 0 },
};

export const SlidePanel = ({
    children,
    className,
    direction = "left",
}: {
    children: React.ReactNode;
    className?: string;
    direction?: "left" | "right";
}) => (
    <motion.div
        initial="hidden"
        animate="visible"
        exit="exit"
        variants={{
            hidden: { x: direction === "left" ? -300 : 300, opacity: 0 },
            visible: { x: 0, opacity: 1 },
            exit: { x: direction === "left" ? -300 : 300, opacity: 0 },
        }}
        transition={springConfig.gentle}
        className={className}
    >
        {children}
    </motion.div>
);

// ============================================
// Presence Wrapper (AnimatePresence helper)
// ============================================
export const Presence = ({
    children,
    show,
}: {
    children: React.ReactNode;
    show: boolean;
}) => (
    <AnimatePresence mode="wait">
        {show && children}
    </AnimatePresence>
);

// Re-export motion and AnimatePresence for convenience
export { motion, AnimatePresence };

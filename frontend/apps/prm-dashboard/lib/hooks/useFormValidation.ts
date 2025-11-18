import { useState, useCallback } from 'react';
import { z } from 'zod';

type ValidationErrors<T> = {
  [K in keyof T]?: string;
};

interface UseFormValidationOptions<T> {
  schema: z.ZodSchema<T>;
  onSubmit: (data: T) => void | Promise<void>;
  onError?: (errors: ValidationErrors<T>) => void;
}

export function useFormValidation<T extends Record<string, any>>({
  schema,
  onSubmit,
  onError,
}: UseFormValidationOptions<T>) {
  const [errors, setErrors] = useState<ValidationErrors<T>>({});
  const [isValidating, setIsValidating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  /**
   * Validate a single field
   */
  const validateField = useCallback(
    (name: keyof T, value: any): string | undefined => {
      try {
        // Extract the field schema
        const fieldSchema = (schema as any).shape?.[name];
        if (!fieldSchema) return undefined;

        // Validate the field
        fieldSchema.parse(value);
        return undefined;
      } catch (error) {
        if (error instanceof z.ZodError) {
          return error.errors[0]?.message;
        }
        return 'Validation error';
      }
    },
    [schema]
  );

  /**
   * Validate all fields
   */
  const validateForm = useCallback(
    (data: Partial<T>): { isValid: boolean; errors: ValidationErrors<T> } => {
      try {
        schema.parse(data);
        return { isValid: true, errors: {} };
      } catch (error) {
        if (error instanceof z.ZodError) {
          const fieldErrors: ValidationErrors<T> = {};
          error.errors.forEach((err) => {
            const fieldName = err.path[0] as keyof T;
            if (fieldName) {
              fieldErrors[fieldName] = err.message;
            }
          });
          return { isValid: false, errors: fieldErrors };
        }
        return { isValid: false, errors: {} };
      }
    },
    [schema]
  );

  /**
   * Handle field blur - validate on blur
   */
  const handleBlur = useCallback(
    (name: keyof T, value: any) => {
      const error = validateField(name, value);
      setErrors((prev) => ({
        ...prev,
        [name]: error,
      }));
    },
    [validateField]
  );

  /**
   * Handle field change - clear error on change
   */
  const handleChange = useCallback((name: keyof T) => {
    setErrors((prev) => ({
      ...prev,
      [name]: undefined,
    }));
  }, []);

  /**
   * Handle form submission
   */
  const handleSubmit = useCallback(
    async (data: Partial<T>) => {
      setIsValidating(true);
      const { isValid, errors: validationErrors } = validateForm(data);

      if (!isValid) {
        setErrors(validationErrors);
        setIsValidating(false);
        onError?.(validationErrors);
        return;
      }

      setErrors({});
      setIsValidating(false);
      setIsSubmitting(true);

      try {
        await onSubmit(data as T);
      } catch (error) {
        console.error('Form submission error:', error);
      } finally {
        setIsSubmitting(false);
      }
    },
    [validateForm, onSubmit, onError]
  );

  /**
   * Reset form errors
   */
  const resetErrors = useCallback(() => {
    setErrors({});
  }, []);

  /**
   * Set custom error
   */
  const setFieldError = useCallback((name: keyof T, message: string) => {
    setErrors((prev) => ({
      ...prev,
      [name]: message,
    }));
  }, []);

  return {
    errors,
    isValidating,
    isSubmitting,
    validateField,
    validateForm,
    handleBlur,
    handleChange,
    handleSubmit,
    resetErrors,
    setFieldError,
  };
}

/**
 * Helper hook for simple form validation without submission
 */
export function useFieldValidation<T>(schema: z.ZodSchema<T>) {
  const [error, setError] = useState<string | undefined>();

  const validate = useCallback(
    (value: T): boolean => {
      try {
        schema.parse(value);
        setError(undefined);
        return true;
      } catch (err) {
        if (err instanceof z.ZodError) {
          setError(err.errors[0]?.message);
        }
        return false;
      }
    },
    [schema]
  );

  const clearError = useCallback(() => {
    setError(undefined);
  }, []);

  return { error, validate, clearError };
}

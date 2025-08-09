"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoginForm } from "@/components/forms/LoginForm";
import { TwoFactorForm } from "@/components/forms/TwoFactorForm";
import type {
  LoginFormData,
  LoginResponse,
  TwoFactorFormData,
  TwoFactorResponse,
} from "@/types/auth";

enum AuthStep {
  LOGIN = "login",
  TWO_FACTOR = "two_factor",
}

export default function LoginPage() {
  const [currentStep, setCurrentStep] = useState<AuthStep>(AuthStep.LOGIN);
  const [tempToken, setTempToken] = useState<string | null>(null);

  const handleLogin = async (data: LoginFormData): Promise<LoginResponse> => {
    try {
      // Use the auth store directly - no need for manual API calls
      const { default: useAuthStore } = await import("@/store/authStore");
      const authStore = useAuthStore.getState();

      const result = await authStore.login(data);

      if (result.requires_2fa && result.temp_token) {
        setTempToken(result.temp_token);
        setCurrentStep(AuthStep.TWO_FACTOR);
        return { requires_2fa: true, temp_token: result.temp_token };
      } else {
        // Redirect to dashboard on successful login
        window.location.href = "/dashboard";
        return { requires_2fa: false };
      }
    } catch (error) {
      throw error;
    }
  };

  const handleTwoFactor = async (
    data: TwoFactorFormData,
  ): Promise<TwoFactorResponse> => {
    if (!tempToken) {
      throw new Error("Token temporário não encontrado");
    }

    try {
      // Use the auth store for 2FA verification
      const { default: useAuthStore } = await import("@/store/authStore");
      const authStore = useAuthStore.getState();

      await authStore.verify2FA(data, tempToken);

      // Redirect to dashboard on successful 2FA verification
      window.location.href = "/dashboard";

      // Return mock response for type compatibility
      return {
        access_token: "verified",
        token_type: "bearer",
        expires_in: 3600,
        user: authStore.user!,
      };
    } catch (error) {
      throw error;
    }
  };

  const handleBackToLogin = async () => {
    // Clear local state
    setCurrentStep(AuthStep.LOGIN);
    setTempToken(null);

    // Clear auth store 2FA state
    const { default: useAuthStore } = await import("@/store/authStore");
    const authStore = useAuthStore.getState();
    authStore.setRequires2FA(false);
    authStore.setTempToken(null);
  };

  const handleLoginError = (error: string) => {
    console.error("Login error:", error);
    // Error is already displayed by the form component
  };

  const handleTwoFactorError = (error: string) => {
    console.error("2FA error:", error);
    // Error is already displayed by the form component
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight">IAM Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Sistema de Gestão de Identidade e Acesso
          </p>
        </div>

        {currentStep === AuthStep.LOGIN && (
          <Card>
            <CardHeader className="text-center">
              <CardTitle>Entrar na sua conta</CardTitle>
              <CardDescription>
                Digite suas credenciais para acessar o sistema
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LoginForm onSubmit={handleLogin} onError={handleLoginError} />
            </CardContent>
          </Card>
        )}

        {currentStep === AuthStep.TWO_FACTOR && (
          <TwoFactorForm
            onSubmit={handleTwoFactor}
            onError={handleTwoFactorError}
            onBack={handleBackToLogin}
          />
        )}

        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>
            Problemas para acessar? Entre em contato com o administrador do
            sistema.
          </p>
        </div>
      </div>
    </div>
  );
}

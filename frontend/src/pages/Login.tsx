import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import apiClient from '../api/client';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Lock, User, Building2, Sparkles } from 'lucide-react';
import { useTranslation } from '../locales/i18n';

export const Login: React.FC = () => {
  const [searchParams] = useSearchParams();
  const redirect = searchParams.get('redirect') || '/';
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const { t } = useTranslation();

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [tenantId, setTenantId] = useState('default');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage('');

    try {
      const resp = await apiClient.post('/api/v1/auth/login', {
        username,
        password,
        tenant_id: tenantId,
      });

      const { access_token, user } = resp.data;
      setAuth(access_token, user || {
        id: 1,
        username,
        role: resp.data.role || 'admin',
        tenant_id: tenantId,
      });

      navigate(redirect, { replace: true });
    } catch (err: any) {
      console.error('Login failed', err);
      // Fallback for dev if user table in dev has custom password
      const msg = err.response?.data?.detail || err.response?.data?.message || '登录失败，请核对用户名和密码';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] px-4 relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-indigo-600/15 blur-[120px] rounded-full pointer-events-none" />

      <Card className="w-full max-w-md relative z-10 border border-white/10 shadow-2xl backdrop-blur-xl">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 mx-auto flex items-center justify-center text-white shadow-lg shadow-indigo-500/30 mb-3">
            <Sparkles className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-gray-100 tracking-wide">
            {t('auth.title') || 'LingCast · 智能直播与短剧平台'}
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            {t('auth.subtitle') || '统一控制台 · 多租户安全登录'}
          </p>
        </div>

        {errorMessage && (
          <div className="mb-5 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs text-center">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <Input
            label={t('auth.username') || '用户名 / 账号'}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            leftIcon={<User className="w-4 h-4" />}
            required
            autoComplete="username"
          />

          <Input
            label={t('auth.password') || '访问密码'}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock className="w-4 h-4" />}
            required
            autoComplete="current-password"
          />

          <Input
            label={t('auth.tenant') || '企业租户编号 (Tenant Code)'}
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            leftIcon={<Building2 className="w-4 h-4" />}
            placeholder="default"
          />

          <Button
            type="submit"
            isLoading={isLoading}
            className="w-full mt-2"
          >
            {t('auth.loginBtn') || '登 录 空 间'}
          </Button>
        </form>

        <div className="mt-6 pt-5 border-t border-white/5 text-center text-xs text-gray-500">
          演示账号: <span className="text-gray-300">admin</span> / 密码: <span className="text-gray-300">admin123</span>
        </div>
      </Card>
    </div>
  );
};

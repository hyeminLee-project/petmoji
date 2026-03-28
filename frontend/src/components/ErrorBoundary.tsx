"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-md mx-auto mt-20 p-8 bg-white rounded-2xl shadow-lg text-center">
          <div className="text-5xl mb-4">😿</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">
            문제가 발생했어요
          </h2>
          <p className="text-gray-500 mb-6 text-sm">
            {this.state.error?.message || "알 수 없는 오류가 발생했습니다"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-xl transition-colors cursor-pointer"
          >
            다시 시도하기
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

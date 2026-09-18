// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { LoginPage } from './LoginPage'

const signInMock = vi.fn()
const signUpMock = vi.fn()

vi.mock('./useAuth', () => ({
  useAuth: () => ({
    status: 'signedOut',
    error: null,
    signIn: signInMock,
    signUp: signUpMock,
  }),
}))

function fillAndSubmit(email: string, password: string) {
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: email } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: password } })
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
}

describe('LoginPage', () => {
  beforeEach(() => {
    signInMock.mockReset()
    signUpMock.mockReset()
  })

  it('calls signIn with the entered credentials', async () => {
    signInMock.mockResolvedValue(undefined)
    renderWithProviders(<LoginPage />)

    fillAndSubmit('vedant@example.com', 'hunter22')

    await waitFor(() =>
      expect(signInMock).toHaveBeenCalledWith('vedant@example.com', 'hunter22'),
    )
  })

  it('switches to sign-up mode and calls signUp instead', async () => {
    signUpMock.mockResolvedValue(undefined)
    renderWithProviders(<LoginPage />)

    fireEvent.click(screen.getByText("Don't have an account? Sign up"))
    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'new@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'hunter22' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create account' }))

    await waitFor(() =>
      expect(signUpMock).toHaveBeenCalledWith('new@example.com', 'hunter22'),
    )
    expect(signInMock).not.toHaveBeenCalled()
  })

  it('surfaces a rejected sign-in instead of failing silently', async () => {
    signInMock.mockRejectedValue(new Error('Invalid login credentials'))
    renderWithProviders(<LoginPage />)

    fillAndSubmit('vedant@example.com', 'wrong-password')

    expect(await screen.findByText('Invalid login credentials')).toBeInTheDocument()
  })
})

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ClientForm } from '../ClientForm'

describe('ClientForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
    mockOnCancel.mockClear()
  })

  describe('Renderização', () => {
    it('deve renderizar todos os campos obrigatórios', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/cpf/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/data de nascimento/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /salvar cliente/i })).toBeInTheDocument()
    })

    it('deve renderizar título "Novo Cliente" por padrão', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      expect(screen.getByText('Novo Cliente')).toBeInTheDocument()
    })

    it('deve renderizar título "Editar Cliente" quando há dados iniciais', () => {
      const initialData = { name: 'João Silva', cpf: '11144477735' }
      render(<ClientForm onSubmit={mockOnSubmit} initialData={initialData} />)
      
      expect(screen.getByText('Editar Cliente')).toBeInTheDocument()
    })

    it('deve renderizar botão cancelar quando onCancel é fornecido', () => {
      render(<ClientForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
      
      expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
    })
  })

  describe('Validação de CPF (@brazilian-utils)', () => {
    it('deve formatar CPF automaticamente durante digitação', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const cpfInput = screen.getByLabelText(/cpf/i)
      
      // Digitar CPF sem formatação
      await user.type(cpfInput, '11144477735')
      
      // Deve formatar automaticamente
      expect(cpfInput).toHaveValue('111.444.777-35')
    })

    it('deve mostrar indicador visual para CPF válido', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const cpfInput = screen.getByLabelText(/cpf/i)
      
      // Digitar CPF válido
      await user.type(cpfInput, '11144477735')
      
      // Deve mostrar indicador de sucesso
      await waitFor(() => {
        expect(screen.getByText('✓')).toBeInTheDocument()
        expect(screen.getByText(/cpf válido.*@brazilian-utils/i)).toBeInTheDocument()
      })
    })

    it('deve mostrar indicador visual para CPF inválido', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const cpfInput = screen.getByLabelText(/cpf/i)
      
      // Digitar CPF inválido
      await user.type(cpfInput, '11111111111')
      
      // Deve mostrar indicador de erro
      await waitFor(() => {
        expect(screen.getByText('✗')).toBeInTheDocument()
      })
    })

    it('deve rejeitar CPF com todos os dígitos iguais', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const cpfInput = screen.getByLabelText(/cpf/i)
      const submitButton = screen.getByRole('button', { name: /salvar cliente/i })
      
      // Preencher formulário com CPF inválido
      await user.type(screen.getByLabelText(/nome completo/i), 'João Silva')
      await user.type(cpfInput, '11111111111')
      await user.type(screen.getByLabelText(/data de nascimento/i), '1990-01-01')
      
      // Botão deve permanecer desabilitado
      expect(submitButton).toBeDisabled()
      
      // Deve mostrar mensagem de erro
      await waitFor(() => {
        expect(screen.getByText(/cpf inválido/i)).toBeInTheDocument()
      })
    })

    it('deve aceitar CPF válido do ClientFactory', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const cpfInput = screen.getByLabelText(/cpf/i)
      
      // Usar CPF válido do backend (ClientFactory sample)
      await user.type(cpfInput, '11144477735')
      
      // Deve ser aceito
      await waitFor(() => {
        expect(screen.getByText('✓')).toBeInTheDocument()
      })
    })
  })

  describe('Validação de Nome', () => {
    it('deve rejeitar nome muito curto', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const nameInput = screen.getByLabelText(/nome completo/i)
      
      await user.type(nameInput, 'A')
      await user.tab() // Sair do campo para triggerar validação
      
      await waitFor(() => {
        expect(screen.getByText(/nome deve ter pelo menos 2 caracteres/i)).toBeInTheDocument()
      })
    })

    it('deve rejeitar nome muito longo', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const nameInput = screen.getByLabelText(/nome completo/i)
      const longName = 'A'.repeat(101)
      
      await user.type(nameInput, longName)
      await user.tab()
      
      await waitFor(() => {
        expect(screen.getByText(/nome deve ter no máximo 100 caracteres/i)).toBeInTheDocument()
      })
    })
  })

  describe('Validação de Data de Nascimento', () => {
    it('deve rejeitar pessoa muito nova (menos de 16 anos)', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const today = new Date()
      const youngDate = new Date(today.getFullYear() - 15, today.getMonth(), today.getDate())
      const dateString = youngDate.toISOString().split('T')[0]
      
      await user.type(screen.getByLabelText(/data de nascimento/i), dateString || '')
      await user.tab()
      
      await waitFor(() => {
        expect(screen.getByText(/cliente deve ter entre 16 e 120 anos/i)).toBeInTheDocument()
      })
    })

    it('deve rejeitar pessoa muito velha (mais de 120 anos)', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const today = new Date()
      const oldDate = new Date(today.getFullYear() - 121, today.getMonth(), today.getDate())
      const dateString = oldDate.toISOString().split('T')[0]
      
      await user.type(screen.getByLabelText(/data de nascimento/i), dateString || '')
      await user.tab()
      
      await waitFor(() => {
        expect(screen.getByText(/cliente deve ter entre 16 e 120 anos/i)).toBeInTheDocument()
      })
    })
  })

  describe('Submissão do Formulário', () => {
    it('deve chamar onSubmit com dados corretos e CPF sem formatação', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      // Preencher formulário válido
      await user.type(screen.getByLabelText(/nome completo/i), 'João da Silva Santos')
      await user.type(screen.getByLabelText(/cpf/i), '11144477735')
      await user.type(screen.getByLabelText(/data de nascimento/i), '1990-01-01')
      
      // Submeter formulário
      const submitButton = screen.getByRole('button', { name: /salvar cliente/i })
      await waitFor(() => expect(submitButton).not.toBeDisabled())
      await user.click(submitButton)
      
      // Verificar dados submetidos
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          name: 'João da Silva Santos',
          cpf: '11144477735', // CPF sem formatação
          birthDate: '1990-01-01'
        })
      })
    })

    it('deve desabilitar botão quando formulário é inválido', async () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const submitButton = screen.getByRole('button', { name: /salvar cliente/i })
      
      // Botão deve estar desabilitado inicialmente
      expect(submitButton).toBeDisabled()
    })

    it('deve mostrar estado de loading', () => {
      render(<ClientForm onSubmit={mockOnSubmit} isLoading={true} />)
      
      expect(screen.getByText('Salvando...')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /salvando/i })).toBeDisabled()
    })
  })

  describe('Integração com Backend', () => {
    it('deve usar mesma validação CPF do backend (@brazilian-utils)', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      // Testar CPFs que sabemos que são válidos no backend
      const validCPFs = [
        '11144477735',  // Valid CPF 1 (ClientFactory sample)
        '79842946908',  // Valid CPF 2 (ClientFactory sample)
        '62974875297',  // Valid CPF 3 (ClientFactory sample)
      ]
      
      const cpfInput = screen.getByLabelText(/cpf/i)
      
      for (const cpf of validCPFs) {
        // Limpar campo
        await user.clear(cpfInput)
        
        // Testar CPF
        await user.type(cpfInput, cpf)
        
        // Deve ser válido
        await waitFor(() => {
          expect(screen.getByText('✓')).toBeInTheDocument()
        })
      }
    })
  })

  describe('Acessibilidade', () => {
    it('deve ter labels corretos para todos os campos', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/cpf/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/data de nascimento/i)).toBeInTheDocument()
    })

    it('deve mostrar mensagens de erro em elementos acessíveis', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)
      
      const nameInput = screen.getByLabelText(/nome completo/i)
      
      await user.type(nameInput, 'A')
      await user.tab()
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/nome deve ter pelo menos 2 caracteres/i)
        expect(errorMessage).toBeInTheDocument()
        expect(errorMessage).toHaveClass('text-red-600')
      })
    })
  })
})
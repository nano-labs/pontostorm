# -*- encoding: utf-8 -*-


def context(request):
    '''
    Define um contexto de variaveis acessíveis em todas as views.
    '''
    return {'generic_viarable': 'variavel do context processor'}

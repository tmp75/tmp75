# Personalizar o perfil

O GitHub mostra este README no perfil quando os ficheiros estão na raiz do repositório público `tmp75/tmp75`, na branch principal `main`.

Edite `profile.json` para atualizar os textos e os dados que pretende apresentar. Use apenas informações que deseja tornar públicas. A arte do avatar está no ficheiro `assets/avatar.txt`; `assets/avatar-tones.json` guarda o tom de cinzento de cada caractere. Os dois ficheiros devem ter as mesmas dimensões. Para usar um ASCII simples com uma só cor, substitua `avatar.txt` e remova `avatar-tones.json`.

Nesta versão, `Host` e `Kernel` descrevem a criação por vibe coding com IA. Os campos `Stack.*` mostram as tecnologias dos projetos, sem indicar níveis de domínio individual. `Stars.Owned` soma as estrelas dos seus repositórios públicos, excluindo forks; `Repos.Public` inclui todos os seus repositórios públicos, incluindo este perfil e forks.

## Atualização

O workflow **Update profile** atualiza os dados públicos diariamente às 06:23 UTC. Também pode executá-lo em **Actions → Update profile → Run workflow**. Alterações na configuração, no script ou em `avatar.txt` iniciam uma atualização ao serem enviadas para `main`.

Para gerar os ficheiros localmente, com Python 3.12:

```sh
python scripts/update_profile.py --refresh
```

Não são necessárias bibliotecas adicionais. O Actions usa o `GITHUB_TOKEN` temporário para consultar a API do GitHub e enviar o commit, evitando o limite reduzido das consultas anónimas. O script consulta os endpoints públicos e exclui explicitamente repositórios privados das estatísticas; não guarda o token. Localmente, funciona sem token, dentro do limite de consultas anónimas. O workflow guarda apenas o README, os quatro SVGs e `assets/stats.json`, quando houver alterações. Se outro commit chegar antes do envio, o Git recusa sobrescrevê-lo; execute novamente o workflow.

## Uptime

Sem data de nascimento, o uptime representa o tempo desde a criação da conta GitHub. Para mostrar a idade, pode definir `birth_date` em `profile.json`, no formato `AAAA-MM-DD`, ou criar o segredo opcional `PROFILE_BIRTH_DATE` em **Settings → Secrets and variables → Actions → New repository secret**.

O segredo evita guardar a data de nascimento no código, mas a idade exata publicada permite deduzi-la. Deixe este campo vazio se preferir apresentar apenas a idade da conta.

O retrato usa animação CSS dentro do SVG, sem JavaScript nem recursos externos. `scripts/matrix_portrait.py` mantém o ASCII visível e faz a chuva de código brilhar mais sobre a figura. A preferência do sistema por movimento reduzido mostra a versão parada. As cores dos dados são definidas no início de `scripts/update_profile.py`.

O uptime e as estatísticas mudam após cada atualização do workflow. O Actions grava primeiro os SVGs e depois aponta o README para o commit exato desses ficheiros, evitando o cache da branch principal. Quando os SVGs não mudam, mantém a referência existente. O agendamento do GitHub Actions pode sofrer atrasos; a execução manual permite atualizar quando necessário.

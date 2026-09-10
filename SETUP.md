# Personalizar o perfil

O GitHub mostra este README no perfil quando os ficheiros estão na raiz do repositório público `tmp75/tmp75`, na branch principal `main`.

Edite `profile.json` para atualizar os textos e os dados que pretende apresentar. Use apenas informações que deseja tornar públicas. A arte do avatar está no ficheiro `avatar.txt` incluído em `assets`; pode substituir o seu conteúdo mantendo os espaços e as quebras de linha.

Nesta versão, `Host` e `Kernel` descrevem o VibeDeck, e os campos `Code.Projects` e `Web.Projects` mostram a stack desse projeto público. Pode substituí-los pela sua atuação profissional. `Stars.Owned` soma as estrelas dos seus repositórios públicos, excluindo forks; `Repos.Public` inclui todos os seus repositórios públicos, incluindo este perfil e forks.

## Atualização

O workflow **Update profile** atualiza os dados públicos diariamente às 06:23 UTC. Também pode executá-lo em **Actions → Update profile → Run workflow**. Alterações na configuração, no script ou em `avatar.txt` iniciam uma atualização ao serem enviadas para `main`.

Para gerar os ficheiros localmente, com Python 3.12:

```sh
python scripts/update_profile.py --refresh
```

Não são necessárias bibliotecas adicionais. A consulta usa a API pública do GitHub sem autenticação. O `GITHUB_TOKEN` é usado apenas para enviar o commit com os ficheiros gerados; não é enviado às consultas de estatísticas. O workflow guarda apenas o README, os dois SVGs e `assets/stats.json`, quando houver alterações. Se outro commit chegar antes do envio, o Git recusa sobrescrevê-lo; execute novamente o workflow.

## Uptime

Sem data de nascimento, o uptime representa o tempo desde a criação da conta GitHub. Para mostrar a idade, pode definir `birth_date` em `profile.json`, no formato `AAAA-MM-DD`, ou criar o segredo opcional `PROFILE_BIRTH_DATE` em **Settings → Secrets and variables → Actions → New repository secret**.

O segredo evita guardar a data de nascimento no código, mas a idade exata publicada permite deduzi-la. Deixe este campo vazio se preferir apresentar apenas a idade da conta.

Os ficheiros gerados são imagens estáticas: o uptime e as estatísticas mudam após cada atualização. O agendamento do GitHub Actions pode sofrer atrasos; a execução manual permite atualizar quando necessário.

# git example

create a folder /tmp/example
```
mkdir /tmp/example
cd /tmp/example
```


create main repo
```
mkdir myproject
cd myproject
git init
echo "# myproject" >> README.md
git add README.md
git commit -m "init"

```


create two developers A and B
```
cd ..
git clone myproject A
git clone myproject B

```

inspect A
```
cd A
git remote -v

origin	/tmp/myproject (fetch)
origin	/tmp/myproject (push)

# note origin repo

```


A create **devel** branch
```
git branch develop
git checkout develop
```

push local branch develop to origin
```
git push --set-upstream origin develop
```


B sync with remote myproject because of new remote branch
```
cd ../B
git fetch -v

From /tmp/myproject
 = [up to date]      master     -> origin/master
 * [new branch]      develop    -> origin/develop

```

inspect B
```
git remote -v
git branch -a

```

per annullare l'ultima modifica:
```
git checkout README.md
```

Da Github:
New issue: per creare delle attività da fare sul progetto
Tutti possono commentare e fare attività.

## Attività

Programmatore A
Per le attività si apre un nuovo branch (esempio: `documentazione`) per poi fare `merge` in seguito

A modifica README.md
Esegue il commit

```
git checkout develop
git merge documentazione
git branch -d documentazione  #viene eliminato il branch
git branch -a
```

Programmatore B

```
git branch hotfixes
git checkout hotfixes
# modifica README.md dove lo ha modificato A
git commit -m "Modifica documentazione"
git checkout develop
git merge hotfixes
git branch -d hotfixes
git pull  # genera conflitto
git status
git add README.md
git commit
git status
git push
```

Programmatore A: aggiorna modifiche

```
git pull
```

REBASE/MERGE
rebase: git sincronizza il mio branch con il remoto e poi applica le modifiche fatte. Altera il mio branch locale perché porta l'history del branch develop al branch locale
merge: più adatto a gruppi di lavoro numerosi

Da VSCode 

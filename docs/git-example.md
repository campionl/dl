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


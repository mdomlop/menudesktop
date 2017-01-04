exe='menudesktop.py'

install:
	install -m 755 $(exe) /usr/bin/
uninstall:
	rm /usr/bin/$(exe)
togit:
	git add .
	git commit -m "Updated from makefile"
	git push origin

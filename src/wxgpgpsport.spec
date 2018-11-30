# -*- mode: python -*-

block_cipher = None


a = Analysis(['wxgpgpsport.py'],
             pathex=['./modules/', './plugins/', '/Volumes/USB2G_LN/wxgpx-phoenix/src'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=['FixTk', 'tcl', '_tkinter', 'tkinter', 'Tkinter', 'tk', 'pubsub', 'smokesignal'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='wxgpgpsport',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='images/Map.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='wxgpgpsport')
app = BUNDLE(coll,
             name='wxgpgpsport.app',
             icon='./images/Map.ico',
             bundle_identifier=None)

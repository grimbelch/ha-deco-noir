"""Copy only theme assets to HA through the existing Unraid guest-agent helper."""
import base64, json, pathlib, subprocess, tempfile, sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
files=['themes/les_saisons.yaml','www/seasons/portraits.png','www/seasons/headers-v3.png','www/seasons/seasons-card.js','www/seasons/display.ttf','www/seasons/OFL.txt','themes/cogitator.yaml','www/cogitator/cogitator-card.js','www/cogitator/title.ttf','www/cogitator/data.ttf','www/cogitator/cog-skull.png','www/cogitator/OFL-PirataOne.txt','www/cogitator/OFL-ChakraPetch.txt']
if '--cogitator' in sys.argv:
    files=[f for f in files if 'cogitator' in f or f=='www/seasons/seasons-card.js']
if '--code-only' in sys.argv:
    files=['www/seasons/seasons-card.js']
if '--picker' in sys.argv:       # Deco theme dropdown card
    files=['www/deco/deco-theme-picker.js']
if '--floorplans' in sys.argv:   # per-theme floor plan SVGs and light-pool overlays
    files=sorted(f.relative_to(ROOT).as_posix() for f in (ROOT/'www'/'deco').glob('*.svg') if f.name.startswith(('floor_','glow_')))
payload={f:base64.b64encode((ROOT/f).read_bytes()).decode() for f in files}
php='''<?php
function agent($execute,$args){
 $r=json_decode(shell_exec('virsh qemu-agent-command HomeAssistant '.escapeshellarg(json_encode(['execute'=>$execute,'arguments'=>$args]))),true);
 if(isset($r['error']) || !array_key_exists('return',$r)) throw new Exception(json_encode($r));
 return $r['return'];
}
$files=json_decode(file_get_contents('/tmp/seasons_payload.json'),true);
foreach($files as $name=>$data){
 if($name!=='www/deco/deco-theme-picker.js' && !preg_match('#^www/deco/(floor|glow)_[a-z0-9_]+\.svg$#',$name) && !in_array($name,['themes/les_saisons.yaml','www/seasons/portraits.png','www/seasons/headers-v3.png','www/seasons/seasons-card.js','www/seasons/display.ttf','www/seasons/OFL.txt','themes/cogitator.yaml','www/cogitator/cogitator-card.js','www/cogitator/title.ttf','www/cogitator/data.ttf','www/cogitator/cog-skull.png','www/cogitator/OFL-PirataOne.txt','www/cogitator/OFL-ChakraPetch.txt'])) throw new Exception('Unexpected path');
 $path='/mnt/data/supervisor/homeassistant/'.$name;
 $h=agent('guest-file-open',['path'=>$path,'mode'=>'w']);
 try { foreach(str_split(base64_decode($data),24576) as $part) {
   $r=agent('guest-file-write',['handle'=>$h,'buf-b64'=>base64_encode($part)]);
   if($r['count']!==strlen($part)) throw new Exception('Short write');
 }} finally { agent('guest-file-close',['handle'=>$h]); }
 echo 'Installed '.$name."\\n";
}
?>'''
with tempfile.TemporaryDirectory() as folder:
    f=pathlib.Path(folder)/'seasons_payload.json';f.write_text(json.dumps(payload))
    p=pathlib.Path(folder)/'seasons_copy.php';p.write_text(php)
    subprocess.run(['scp',str(f),str(p),'root@192.168.0.100:/tmp/'],check=True)
    # Guest directories are prepared using the existing helper before invoking this script.
    subprocess.run(['ssh','root@192.168.0.100','php /tmp/seasons_copy.php'],check=True)
    subprocess.run(['ssh','root@192.168.0.100','rm -f /tmp/seasons_copy.php /tmp/seasons_payload.json /tmp/install_seasons_assets.py'],check=True)

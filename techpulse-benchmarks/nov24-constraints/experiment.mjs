// Node 24; pass the unpacked @huggingface/transformers-structured-output@4.3.2 directory.
import { registerHooks } from 'node:module';
import { writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
registerHooks({resolve(spec, context, next) {
  if (spec.startsWith('.') && !spec.endsWith('.ts')) spec += '.ts';
  return next(spec,context);
}});
const engine = await import(pathToFileURL(resolve(process.argv[2],'src/engine/constraint.ts')));
const tokenizer={tokens:Array.from({length:129},(_,i)=>i===128?[]:[i]),eosTokenId:128};
const schema={type:'object',properties:{priority:{type:'string',enum:['low','high']}},required:['priority'],additionalProperties:false};
const modes={object:{type:'json_object'},schema:{type:'json_schema',json_schema:schema}};
const cases=[
 ['Correct label','{"priority":"high"}',true,true],
 ['Wrong label','{"priority":"low"}',true,true],
 ['Unknown label','{"priority":"urgent"}',true,false],
 ['Missing field','{}',true,false],
 ['Extra field','{"priority":"high","note":"ok"}',true,false],
 ['Broken JSON','{"priority":}',false,false]
];
const results=cases.map(([name,s,...expected])=>{
 const accepted=Object.values(modes).map(mode=>{
  const constraint=engine.createTokenConstraint(tokenizer,mode);
  const mask=new Uint32Array(5);
  for(const id of [...Buffer.from(s),128]){
   constraint.fillMask(mask);
   if(!(mask[id>>>5] & (1<<(id%32))))return false;
   constraint.commit(id);
  }
  return true;
 });
 if(JSON.stringify(accepted)!==JSON.stringify(expected))throw Error(name);
 return {name,candidate:s,accepted};
});
writeFileSync(new URL('results.json',import.meta.url),JSON.stringify({version:'4.3.2',expectedPriority:'high',schema,results},null,2));
console.log(results);

import { createHash } from 'node:crypto';
import { Document, HeadingLevel, Packer, Paragraph, TextRun } from 'docx';
import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';
import type { Pool } from 'pg';
import type { EngineeringArtifact } from './engineering-program.js';

export type BinaryDocumentFormat='pdf'|'docx';
export interface BinaryDocumentPackage {
  packageId:string;
  artifactId:string;
  format:BinaryDocumentFormat;
  filename:string;
  mediaType:string;
  contentBase64:string;
  contentHash:string;
  createdAt:string;
  releaseState:'internal_review'|'release_candidate';
  externalActionBlocked:true;
}

export class ControlledDocumentRenderer {
  constructor(private readonly pool:Pool){}

  async render(artifactId:string,format:BinaryDocumentFormat):Promise<BinaryDocumentPackage>{
    const result=await this.pool.query('select artifact_json,approval_state from engineering_artifacts where artifact_id=$1',[artifactId]);
    if(!result.rowCount)throw new Error('Engineering artifact not found.');
    const artifact=result.rows[0].artifact_json as EngineeringArtifact;
    const bytes=format==='pdf'?await renderPdf(artifact):await renderDocx(artifact);
    const createdAt=new Date().toISOString();
    const contentHash=hash(bytes);
    const releaseState=result.rows[0].approval_state==='technical_review'?'release_candidate':'internal_review';
    const pkg:BinaryDocumentPackage={packageId:`BINARY-${contentHash.slice(0,20)}`,artifactId,format,filename:`${artifact.type}-${artifact.artifactId}.${format}`,mediaType:format==='pdf'?'application/pdf':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',contentBase64:Buffer.from(bytes).toString('base64'),contentHash,createdAt,releaseState,externalActionBlocked:true};
    await this.pool.query(`insert into artifact_binary_exports(package_id,artifact_id,format,filename,media_type,content_bytes,content_hash,release_state,external_action_blocked,created_at) values($1,$2,$3,$4,$5,$6,$7,$8,true,$9) on conflict(package_id) do nothing`,[pkg.packageId,artifactId,format,pkg.filename,pkg.mediaType,Buffer.from(bytes),contentHash,releaseState,createdAt]);
    await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('engineering.binary_export.created',$1,$2)`,[artifactId,{packageId:pkg.packageId,format,releaseState,externalActionBlocked:true}]);
    return pkg;
  }
}

async function renderPdf(artifact:EngineeringArtifact):Promise<Uint8Array>{
  const pdf=await PDFDocument.create();
  const font=await pdf.embedFont(StandardFonts.Helvetica);
  const bold=await pdf.embedFont(StandardFonts.HelveticaBold);
  const page=pdf.addPage([612,792]);
  const margin=54,maxWidth=504;
  let y=738;
  page.drawText(artifact.title,{x:margin,y,size:18,font:bold,color:rgb(0,0,0)});y-=30;
  const lines=[`Artifact ID: ${artifact.artifactId}`,`Opportunity: ${artifact.opportunityId}`,`Specification: ${artifact.specificationId}`,`Approval state: ${artifact.approvalState}`,'External action blocked: true','',...wrap(JSON.stringify(artifact.content,null,2),82)];
  for(const line of lines){if(y<54)break;page.drawText(line,{x:margin,y,size:9,font,maxWidth});y-=12;}
  return pdf.save();
}

async function renderDocx(artifact:EngineeringArtifact):Promise<Uint8Array>{
  const document=new Document({sections:[{children:[new Paragraph({text:artifact.title,heading:HeadingLevel.TITLE}),new Paragraph({children:[new TextRun({text:`Artifact ID: ${artifact.artifactId}`,bold:true})]}),new Paragraph(`Opportunity: ${artifact.opportunityId}`),new Paragraph(`Specification: ${artifact.specificationId}`),new Paragraph(`Approval state: ${artifact.approvalState}`),new Paragraph('External action blocked: true'),new Paragraph({text:'Content',heading:HeadingLevel.HEADING_1}),...JSON.stringify(artifact.content,null,2).split('\n').map(line=>new Paragraph({children:[new TextRun({text:line,font:'Courier New'})]}))]}]});
  return new Uint8Array(await Packer.toBuffer(document));
}

function wrap(value:string,width:number){const output:string[]=[];for(const raw of value.split('\n')){if(!raw){output.push('');continue;}for(let i=0;i<raw.length;i+=width)output.push(raw.slice(i,i+width));}return output;}
function hash(value:Uint8Array){return createHash('sha256').update(value).digest('hex');}

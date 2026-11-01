import { OpportunityIntakeService } from './intake.js';
import { createBrainPlan, generateBuildSpecification, parseOpportunity } from './pipeline.js';
export class GovernmentOpsRuntime {
    repository;
    intake;
    constructor(repository) {
        this.repository = repository;
        this.intake = new OpportunityIntakeService(repository);
    }
    async handle(request) {
        try {
            if (request.method === 'POST' && request.path === '/api/opportunities/ingest') {
                const envelope = request.body;
                const receipt = await this.intake.ingest(envelope);
                if (receipt.result.disposition !== 'unchanged' && receipt.result.stored.status === 'active') {
                    await this.analyzeAndPlan(receipt.result.stored.opportunity);
                }
                return { status: receipt.result.disposition === 'created' ? 201 : 200, body: receipt };
            }
            const analyze = request.path.match(/^\/api\/opportunities\/([^/]+)\/analyze$/);
            if (request.method === 'POST' && analyze) {
                const stored = await this.repository.getByEventId(decodeURIComponent(analyze[1]));
                if (!stored)
                    return { status: 404, body: { error: 'Opportunity not found' } };
                return { status: 200, body: await this.analyzeAndPlan(stored.opportunity) };
            }
            const state = request.path.match(/^\/api\/opportunities\/([^/]+)\/state$/);
            if (request.method === 'GET' && state) {
                const stored = await this.repository.getByEventId(decodeURIComponent(state[1]));
                return stored ? { status: 200, body: stored } : { status: 404, body: { error: 'Opportunity not found' } };
            }
            return { status: 404, body: { error: 'Route not found' } };
        }
        catch (error) {
            return { status: 400, body: { error: error instanceof Error ? error.message : String(error) } };
        }
    }
    async analyzeAndPlan(opportunity) {
        const analysis = parseOpportunity(opportunity);
        const specification = generateBuildSpecification(analysis);
        const plan = createBrainPlan(specification);
        await this.repository.saveAnalysis(analysis);
        await this.repository.saveSpecification(specification);
        await this.repository.saveBrainPlan(plan);
        await this.repository.appendEvent('opportunity.build_plan.created', opportunity.eventId, { analysis, specification, plan });
        return { analysis, specification, plan };
    }
}
